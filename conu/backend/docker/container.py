"""
Implementation of a docker container
"""
from __future__ import print_function, unicode_literals

import functools
import logging

from docker.errors import NotFound

from conu.apidefs.container import Container
from conu.apidefs.filesystem import Filesystem
from conu.backend.docker.client import get_client
from conu.exceptions import ConuException
from conu.utils import check_port, run_cmd
from conu.utils.probes import Probe

logger = logging.getLogger(__name__)


class DockerRunBuilder(object):
    """
    helper to execute `docker run` -- users can easily change or override anything
    """

    def __init__(self, command=None, additional_opts=None):
        """
        Build `docker run` command

        :param command: list of str, command to run in the container, examples:
            - ["ls", "/"]
            - ["bash", "-c", "ls / | grep bin"]
        :param additional_opts: list of str, additional options for `docker run`
        """
        self.binary = ["docker"]
        self.global_options = []
        self.command = ["container", "run"]
        self.options = additional_opts or []
        self.image_name = None
        self.arguments = command or []

    def __str__(self):
        return str(self.build())

    def build(self):
        return self.binary + self.global_options + self.command + self.options + \
            [self.image_name] + self.arguments


class DockerContainerFS(Filesystem):
    def __init__(self, container, mount_point=None):
        """
        :param container: instance of DockerContainer
        :param mount_point: str, directory where the filesystem will be mounted
        """
        super(DockerContainerFS, self).__init__(container, mount_point=mount_point)
        self.container = container  # convenience

    def __enter__(self):
        cmd = ["atomic", "mount", self.container.get_id(), self.mount_point]
        logger.debug(cmd)
        run_cmd(cmd)
        return super(DockerContainerFS, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        run_cmd(["atomic", "umount", self.mount_point])
        return super(DockerContainerFS, self).__exit__(exc_type, exc_val, exc_tb)


class DockerContainer(Container):
    def __init__(self, image, container_id, name=None, popen_instance=None):
        """
        :param image: DockerImage instance
        :param container_id: str, unique identifier of this container
        :param name: str, pretty container name
        :param popen_instance: instance of Popen (if container was created using method
            `via_binary`, this is the docker client process)
        """
        super(DockerContainer, self).__init__(image, container_id, name)
        self.popen_instance = popen_instance
        self.d = get_client()

    def __repr__(self):
        return "DockerContainer(image=%s, id=%s)" % (self.image, self.get_id())

    def __str__(self):
        return self.get_id()

    def get_id(self):
        """
        get unique identifier of this container

        :return: str
        """
        if self._id is None:
            # FIXME: provide a better error message when key is not defined
            self._id = self.get_metadata(refresh=False)["Id"]
        return self._id

    def inspect(self, refresh=True):
        """
        return cached metadata by default (a convenience method)

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        return self.get_metadata(refresh=refresh)

    def get_metadata(self, refresh=True):
        """
        return cached metadata by default

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        if refresh or not self._metadata:
            ident = self._id or self.name
            if not ident:
                raise ConuException("This container does not have a valid identifier.")
            self._metadata = self.d.inspect_container(ident)
        return self._metadata

    def is_running(self):
        """
        returns True if the container is running, this method should always ask the API and
        should not use a cached value

        :return: bool
        """
        # # TODO: kick-off of https://github.com/fedora-modularity/conu/issues/24
        # import pprint
        # pprint.pprint(self._metadata)
        # cmdline = ["docker", "container", "logs", self.tag]
        # output = run_cmd(cmdline)
        # print(output)
        try:
            return self.get_metadata(refresh=True)["State"]["Running"]
        except NotFound:
            return False

    def get_IPv4s(self):
        """
        Return all known IPv4 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        # FIXME: be graceful in obtaining values from dict: the keys might not be set
        return [x["IPAddress"]
                for x in self.get_metadata(refresh=True)["NetworkSettings"]["Networks"].values()]

    def get_ports(self):
        """
        get ports specified in container metadata

        :return: list of str
        """
        ports = []
        container_ports = self.get_metadata(refresh=True)["NetworkSettings"]["Ports"]
        if not container_ports:
            return ports
        for p in container_ports:
            # TODO: gracefullness, error handling
            ports.append(p.split("/")[0])
        return ports

    def is_port_open(self, port, timeout=2):
        """
        check if given port is open and receiving connections on container ip_address

        :param port: int, container port
        :param timeout: int, how many seconds to wait for connection; defaults to 2
        :return: True if the connection has been established inside timeout, False otherwise
        """
        addresses = self.get_IPv4s()
        if not addresses:
            return False
        return check_port(port, host=addresses[0], timeout=timeout)

    def get_port_mappings(self, port=None):
        """
        for port in container get list of port mappings on host in form:
        {"HostIp": XX, "HostPort": YY};
        when port is None - get all port mappings

        :param port: int or None, container port
        :return: list of dict or None; dict when port=None
        """
        port_mappings = self.get_metadata(refresh=True)["NetworkSettings"]["Ports"]

        if not port:
            return port_mappings

        if str(port) not in self.get_ports():
            return []

        for p in port_mappings:
            if p.split("/")[0] == str(port):
                return port_mappings[p]

    def wait_for_port(self, port, timeout=10, **probe_kwargs):
        """
        block until specified port starts accepting connections, raises an exc ProbeTimeout
        if timeout is reached

        :param port: int, port number
        :param timeout: int or float (seconds), time to wait for establishing the connection
        :param probe_kwargs: arguments passed to Probe constructor
        :return: None
        """
        Probe(timeout=timeout, fnc=functools.partial(self.is_port_open, port), **probe_kwargs).run()

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        # using `docker cp` b/c put_archive is too complicated
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["docker", "cp", src, "%s:%s" % (self.get_id(), dest)]
        run_cmd(cmd)

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container or image to host system.

        :param src: str, path to a file or a directory within container or image
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        # using `docker cp` b/c get_archive is too complicated
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["docker", "cp", "%s:%s" % (self.get_id(), src), dest]
        run_cmd(cmd)

    def start(self):
        """
        start current container - the container has to be created

        :return: None
        """
        self.d.start(self.get_id())

    def execute(self, command, exec_create_kwargs=None, exec_start_kwargs=None):
        """
        execute a command in this container -- the container needs to be running

        :param command: list of str, command to execute in the container
        :param exec_create_kwargs: dict, params to pass to exec_create()
        :param exec_start_kwargs: dict, params to pass to exec_start()
        :return: str (output) or iterator
        """
        exec_create_kwargs = exec_create_kwargs or {}
        exec_start_kwargs = exec_start_kwargs or {}
        exec_i = self.d.exec_create(self.get_id(), command, **exec_create_kwargs)
        response = self.d.exec_start(exec_i, **exec_start_kwargs)
        e_inspect = self.d.exec_inspect(exec_i)
        # FIXME: if not stream
        if e_inspect["ExitCode"]:
            logger.error("command failed: %s", command)
            logger.info("exec metadata: %s", e_inspect)
            logger.debug("output = %s", response)
            raise ConuException("failed to execute command %s", command)
        # maybe return e_inspect too?
        return response

    def logs(self, follow=False):
        """
        get logs from this container

        :param follow: bool, provide iterator if True and follow logs
        :return: str or iterator
        """
        return self.d.logs(self.get_id(), stream=follow, follow=follow)

    def stop(self):
        """
        stop this container

        :return: None
        """
        self.d.stop(self.get_id())

    def kill(self, signal=None):
        """
        send a signal to this container (bear in mind that the process won't have time
        to shutdown properly and your service may end up in an inconsistent state)

        :param signal: str or int, signal to use for killing the container (SIGKILL by default)
        :return: None
        """
        self.d.kill(self.get_id(), signal=signal)

    def delete(self, force=False, volumes=False, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters

        :param force: bool, if container engine supports this, force the functionality
        :param volumes: bool, remove also associated volumes
        :return: None
        """
        self.d.remove_container(self.get_id(), v=volumes, force=force)

    def mount(self, mount_point=None):
        """
        mount container filesystem

        :param mount_point: str, directory where the filesystem will be mounted
        :return: instance of DockerContainerFS
        """
        return DockerContainerFS(self, mount_point=mount_point)

    def get_status(self):
        """
        Get status of container

        :return: one of: 'created', 'restarting', 'running', 'paused', 'exited', 'dead'
        """
        return self.get_metadata(refresh=True)["State"]["Status"]

    def wait(self, timeout=None):
        """
        Block until the container stops, then return its exit code. Similar to
        the ``docker wait`` command.

        :param timeout: int, Request timeout
        :return: int, exit code
        """
        return self.d.wait(self.get_id(), timeout)

    def exit_code(self):
        """
        get exit code of container. Return value is 0 for running and created containers

        :return: int
        """
        return self.get_metadata()["State"]["ExitCode"]

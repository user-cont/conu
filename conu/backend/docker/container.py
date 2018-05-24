# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Implementation of a docker container
"""
from __future__ import print_function, unicode_literals

import functools
import logging
import shutil
import subprocess
from tempfile import mkdtemp

from docker.errors import NotFound

from conu.apidefs.container import Container
from conu.apidefs.image import Image
from conu.apidefs.metadata import ContainerStatus
from conu.apidefs.filesystem import Filesystem
from conu.apidefs.metadata import ContainerMetadata
from conu.backend.docker.client import get_client
from conu.exceptions import ConuException
from conu.utils import check_port, run_cmd, export_docker_container_to_directory
from conu.utils.probes import Probe
from conu.backend.docker.constants import CONU_ARTIFACT_TAG

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
        # there is no `docker container` on centos (docker-1.12.6-71.git3e8e77d.el7.centos.1.x86_64)
        self.command = ["run"]
        self.options = additional_opts or []
        self.image_name = None
        self.arguments = command or []

    def __str__(self):
        return str(self.build())

    def build(self):
        return self.binary + self.global_options + self.command + self.options + \
            ["-l", CONU_ARTIFACT_TAG] + [self.image_name] + self.arguments


class DockerContainerViaExportFS(Filesystem):
    def __init__(self, container, mount_point=None):
        """
        Provide container as an archive

        :param container: instance of DockerContainer
        :param mount_point: str, directory where the filesystem will be made available
        """
        super(DockerContainerViaExportFS, self).__init__(container, mount_point=mount_point)
        self.container = container

    @property
    def mount_point(self):
        if self._mount_point is None:
            # we pick /var/tmp b/c it's not on tmpfs
            self._mount_point = mkdtemp(prefix="conu", dir="/var/tmp")
            self.mount_point_provided = False
        return self._mount_point

    def __enter__(self):
        client = get_client()
        export_docker_container_to_directory(client, self.container, self.mount_point)
        return super(DockerContainerViaExportFS, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.mount_point_provided:
            # some dirs are 0400
            run_cmd(["chmod", "-R", "u+w", self.mount_point])
            shutil.rmtree(self.mount_point)


class DockerContainer(Container):
    def __init__(self, image, container_id, name=None, popen_instance=None, short_metadata=None):
        """
        :param image: DockerImage instance (if None, it will be found from the container itself)
        :param container_id: str, unique identifier of this container
        :param name: str, pretty container name
        :param popen_instance: instance of Popen (if container was created using method
            `via_binary`, this is the docker client process)
        :param short_metadata: dict, metadata obtained from `docker.APIClient.containers()`
        """
        self.d = get_client()
        super(DockerContainer, self).__init__(image, container_id, name)
        self.popen_instance = popen_instance
        # metadata obtained when doing `docker.APIClient().containers()`
        self.short_metadata = short_metadata

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
            self._id = self.inspect(refresh=False)["Id"]
        return self._id

    def inspect(self, refresh=True):
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
            return self.inspect(refresh=True)["State"]["Running"]
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
                for x in self.inspect(refresh=True)["NetworkSettings"]["Networks"].values()]

    def get_IPv6s(self):
        """
        Return all known IPv6 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        # FIXME: be graceful in obtaining values from dict: the keys might not be set
        return [x["GlobalIPv6Address"]
                for x in self.inspect(refresh=True)["NetworkSettings"]["Networks"].values()]

    def get_ports(self):
        """
        get ports specified in container metadata

        :return: list of str
        """
        ports = []
        container_ports = self.inspect(refresh=True)["NetworkSettings"]["Ports"]
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
        Get list of port mappings between container and host. The format of dicts is:

            {"HostIp": XX, "HostPort": YY};

        When port is None - return all port mappings. The container needs
        to be running, otherwise this returns an empty list.

        :param port: int or None, container port
        :return: list of dict or None; dict when port=None
        """
        port_mappings = self.inspect(refresh=True)["NetworkSettings"]["Ports"]

        if not port:
            return port_mappings

        if str(port) not in self.get_ports():
            return []

        for p in port_mappings:
            if p.split("/")[0] == str(port):
                return port_mappings[p]

    def get_image_name(self):
        """
        return name of the container image

        :return: str
        """
        metadata = self.inspect()
        if "Config" in metadata:
            return metadata["Config"].get("Image", None)
        return None

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

    def execute(self, command, blocking=True, exec_create_kwargs=None, exec_start_kwargs=None):
        """
        Execute a command in this container -- the container needs to be running.

        If the command fails, a ConuException is thrown.

        This is a blocking call by default and writes output of the command to logger
        using the INFO level -- this behavior can be changed if you set
        the argument `blocking` to `False`.

        If not blocking, you should consume the returned iterator in order to see logs or know
        when the command finished:

        ::

            for line in container.execute(["ping", "-c", "4", "8.8.8.8"], blocking=False):
                print(line)
            print("command finished")

        :param command: list of str, command to execute in the container
        :param blocking: bool, if True blocks until the command finishes
        :param exec_create_kwargs: dict, params to pass to exec_create()
        :param exec_start_kwargs: dict, params to pass to exec_start()
        :return: iterator if non-blocking or list of bytes if blocking
        """
        logger.info("running command %s", command)

        exec_create_kwargs = exec_create_kwargs or {}
        exec_start_kwargs = exec_start_kwargs or {}
        exec_start_kwargs["stream"] = True  # we want stream no matter what
        exec_i = self.d.exec_create(self.get_id(), command, **exec_create_kwargs)
        output = self.d.exec_start(exec_i, **exec_start_kwargs)
        if blocking:
            response = []
            for line in output:
                response.append(line)
                logger.info("%s", line.decode("utf-8").strip("\n\r"))

            e_inspect = self.d.exec_inspect(exec_i)
            exit_code = e_inspect["ExitCode"]
            if exit_code:
                logger.error("command failed")
                logger.info("exec metadata: %s", e_inspect)
                raise ConuException("failed to execute command %s, exit code %s" % (
                                    command, exit_code))
            return response
        # TODO: for interactive use cases we need to provide API so users can do exec_inspect
        return output

    def logs(self, follow=False):
        """
        Get logs from this container. Every item of the iterator contains one log line
        terminated with a newline. The logs are encoded (they are bytes, not str).

        Let's look at an example::

            image = conu.DockerImage("fedora", tag="27")
            command = ["bash", "-c", "for x in `seq 1 5`; do echo $x; sleep 1; done"]
            container = image.run_via_binary(command=command)
            for line in container.logs(follow=True):
                print(line)

        This will output

        .. code-block:: none

            b'1\\n'
            b'2\\n'
            b'3\\n'
            b'4\\n'
            b'5\\n'

        :param follow: bool, provide new logs as they come
        :return: iterator (of bytes)
        """
        return self.d.logs(self.get_id(), stream=True, follow=follow)

    def logs_in_bytes(self):
        """
        Get output of container in bytes.

        :return: bytes
        """
        logs = self.logs()
        return b"".join(list(logs))

    def logs_unicode(self):
        """
        Get output of container decoded using utf-8.

        :return: str
        """
        logs = self.logs_in_bytes()
        return logs.decode("utf-8")

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
        :return: instance of DockerContainerViaExportFS
        """
        return DockerContainerViaExportFS(self, mount_point=mount_point)

    def get_status(self):
        """
        Get status of container

        :return: one of: 'created', 'restarting', 'running', 'paused', 'exited', 'dead'
        """
        return self.inspect(refresh=True)["State"]["Status"]

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
        return self.inspect()["State"]["ExitCode"]

    def write_to_stdin(self, message):
        """
        Write provided text to container's standard input. In order to make this function work, there needs to be several conditions met:
         * the container needs to be running
         * the container needs to have stdin open
         * the container has to be created using method `run_via_binary_in_foreground`

        For more info see documentation in run_via_binary_in_foreground()

        :param message: str or bytes, text to be written to container standard input
        """
        if not self.is_running():
            raise ConuException(
                "Container must be running")
        if not self.popen_instance:
            raise ConuException(
                "This container doesn't seem to be created using method `run_via_binary_in_foreground`.")
        if not self.popen_instance.stdin:
            raise ConuException(
                "Container should be run with stdin redirection.")

        if not isinstance(message, bytes):
            if isinstance(message, str):
                message = message.encode()
            else:
                raise ConuException(
                    "Message should be an instance of str or bytes")
        try:
            self.popen_instance.stdin.write(message)
            self.popen_instance.stdin.flush()
        except subprocess.CalledProcessError as e:
            raise ConuException(e)

    def get_metadata(self):
        """
        Convert dictionary returned after docker inspect command into instance of ContainerMetadata class
        :return: ContainerMetadata, container metadata instance
        """

        docker_metadata = self.inspect(refresh=True)

        # format of Environment Variables from docker inspect:
        # ['DISTTAG=f26container', 'FGC=f26']
        env_variables = dict()
        for env_variable in docker_metadata['Config']['Env']:
            try:
                env_variables.update({env_variable.split('=', 1)[0]: env_variable.split('=', 1)[1]})
            except IndexError:
                ConuException("Wrong format of environment variable")

        # format of image name from docker inspect:
        # sha256:8f0e66c924c0c169352de487a3c2463d82da24e9442fc097dddaa5f800df7129
        image = Image(docker_metadata['Image'].split(':')[1])

        status = ContainerStatus.get_from_docker(docker_metadata['State']['Status'],
                                                 docker_metadata['State']['ExitCode'])

        try:
            exposed_ports = list(docker_metadata['Config']['ExposedPorts'].keys())
        except KeyError:
            exposed_ports = None

        # format of Port mappings from docker inspect:
        # {'12345/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '123'}, {'HostIp': '0.0.0.0', 'HostPort': '1234'}]}
        port_mappings = dict()

        for key, value in docker_metadata['HostConfig']['PortBindings'].items():
            for item in value:
                if key in port_mappings.keys():
                    if item['HostPort'] is not '':
                        port_mappings[key].append(int(item['HostPort']))
                    else:
                        port_mappings[key].append(None)
                else:
                    if item['HostPort'] is not '':
                        port_mappings.update({key: [int(item['HostPort'])]})
                    else:
                        port_mappings.update({key: [None]})

        container_metadata = ContainerMetadata(
            name=docker_metadata['Name'][1:],  # remove / at the beginning
            identifier=docker_metadata['Id'],
            labels=docker_metadata['Config']['Labels'],
            command=docker_metadata['Config']['Cmd'],
            creation_timestamp=docker_metadata['Created'],
            env_variables=env_variables,
            image=image,
            exposed_ports=exposed_ports,
            port_mappings=port_mappings,
            hostname=docker_metadata['Config']['Hostname'],
            ipv4_addresses=self.get_IPv4s(),
            ipv6_addresses=self.get_IPv6s(),
            status=status)

        return container_metadata



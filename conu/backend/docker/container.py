"""
Implementation of a docker container
"""

import json
import logging
import subprocess

from conu.backend.docker.image import DockerImage
from conu.apidefs.container import Container
from conu.apidefs.exceptions import ConuException
from conu.utils.core import run_cmd


logger = logging.getLogger(__name__)


class DockerRunCommand(object):
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
        if not isinstance(image, DockerImage):
            raise RuntimeError("image argument is not an instance of the DockerImage class")

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
            self._metadata = json.loads(run_cmd("docker container inspect %s" % ident))[0]
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
        except subprocess.CalledProcessError:
            return False

    def get_IPv4s(self):
        """
        Return all knwon IPv4 addresses of this container. It may be possible
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
        for p in self.get_metadata(refresh=True)["NetworkSettings"]["Ports"]:
            # TODO: gracefullness, error handling
            ports.append(p.split("/")[0])
        return ports

    @classmethod
    def run_via_binary(cls, image, run_command_instance, *args, **kwargs):
        """
        create container using provided image and run it in background;
        this method is useful to test real user scenarios when users invoke containers using
        binary

        :param image: instance of Image
        :param run_command_instance: instance of DockerRunCommand
        :return: instance of DockerContainer
        """
        if not isinstance(run_command_instance, DockerRunCommand):
            raise ConuException("run_command_instance needs to be an instance of DockerRunCommand")
        run_command_instance.image_name = image.get_id()
        run_command_instance.options += ["-d"]
        popen_instance = subprocess.Popen(run_command_instance.build(), stdout=subprocess.PIPE)
        container_id = popen_instance.communicate()[0].strip()
        return cls(image, container_id)

    @classmethod
    def run_via_binary_in_foreground(cls, image, run_command_instance, popen_params=None,
                                        container_name=None):
        """
        create container using provided image and run it in foreground;
        this method is useful to test real user scenarios when users invoke containers using
        binary and pass input into the container via STDIN

        :param image: instance of Image
        :param run_command_instance: instance of DockerRunCommand
        :param popen_params: dict, keyword arguments passed to Popen constructor
        :param container_name: str, pretty container identifier
        :return: instance of DockerContainer
        """
        logger.info("run container via binary in foreground")
        if not isinstance(run_command_instance, DockerRunCommand):
            raise ConuException("run_command_instance needs to be an instance of DockerRunCommand")
        popen_params = popen_params or {}
        run_command_instance.image_name = image.get_id()
        if container_name:
            run_command_instance.options += ["--name", container_name]
        logger.debug("command = %s", str(run_command_instance))
        popen_instance = subprocess.Popen(run_command_instance.build(), **popen_params)
        container_id = None
        return cls(image, container_id, popen_instance=popen_instance, name=container_name)

    def start(self):
        """
        start current container

        :return: None
        """
        c = ["docker", "container", "start", self._id]
        run_cmd(c)

    def execute(self, command, shell=True, **kwargs):
        """
        execute a command in this container -- the container needs to be running

        :param command: str, command to execute in the container
        :param shell: bool, invoke the command in shell via '/bin/bash -c'
        :return: str (output) or Popen instance
        """
        c = ["docker", "container", "exec", self._id]
        if shell:
            c += ["/bin/bash", "-c"]
        if isinstance(command, list):
            c += command
        elif isinstance(command, str):
            c.append(command)
        return run_cmd(c, **kwargs)

    # FIXME: implement follow with docker-py
    def logs(self, follow=False):
        """
        get logs from this container

        :param follow: bool, provide iterator if True
        :return: str or iterator
        """
        c = ["docker", "container", "logs", self._id]
        return run_cmd(c)

    def stop(self):
        """
        stop this container

        :return: None
        """
        run_cmd("docker container stop %s" % self._id)

    def rm(self, force=False, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters

        :param force: bool, if container engine supports this, force the functionality
        :return: None
        """
        run_cmd("docker container rm %s%s" % ("-f " if force else "", self._id))

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        run_cmd("docker cp %s %s:%s" % (src, self._id, dest))

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container to host system

        :param src: str, path to a file or a directory within container
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        self.start()
        run_cmd("docker cp %s:%s %s" % (self._id, src, dest))

    def read_file(self, file_path):
        """
        read file specified via 'file_path' and return its content - raises an exc if there is
        an issue with read the file

        :param file_path: str, path to the file to read
        :return: str (not bytes), content of the file
        """
        # since run_cmd does split, we need to wrap like this because the command
        # is actually being wrapped in bash -c -- time for a drink
        try:
            return self.execute(["cat", file_path], shell=False)
        except subprocess.CalledProcessError:
            raise ConuException("There was in issue while accessing file %s" % file_path)

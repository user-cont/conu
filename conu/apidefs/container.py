"""
Abstract class definitions for containers.
"""

# FIXME: TBD
from .image import Image


class BinaryArgsBuilder(object):
    """
    class which helps you build a command so it can be executed via subprocess

    TBD: I think I
    """
    template = "{binary} {global_opts} {cmd} {opts} {args}"
    binary = ""
    global_options = ""
    command = ""
    arguments = ""
    options = ""

    def build(self):
        command = self.template.format(
            binary=self.binary,
            global_opts=self.global_options,
            cmd=self.command,
            opts=self.options,
            args=self.arguments
        )
        return command


class ContainerParameters(object):
    """
    key value store of container parameters

    TBD
    """


class Container(object):
    """
    Container class definition which contains abstract methods. The instances should call the
    constructor
    """
    def __init__(self, image, container_id):
        """
        :param image: Image instance
        :param container_id: str, unique identifier of this container
        """
        if not isinstance(image, Image):
            raise RuntimeError("image argument is not an instance of Image class")
        self.image = image
        self.container_id = container_id
        self._metadata = None

    def get_metadata(self, refresh=False):
        """
        return cached metadata by default

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        raise NotImplementedError("get_metadata method is not implemented")

    def is_running(self):
        """
        returns True if the container is running, this method should always ask the API and
        should not use a cached value

        :return: bool
        """
        raise NotImplementedError("is_running method is not implemented")

    def status(self):
        """
        Provide current, up-to-date status of this container. This method should not use cached
        value. Implementation of this method should clearly state list of possible values
        to get from this method

        :return: str
        """
        raise NotImplementedError("status method is not implemented")

    def get_pid(self):
        """
        get process identifier of the root process in the container

        :return: int
        """
        raise NotImplementedError("get_pid method is not implemented")

    def name(self):
        """
        Return name of this container.

        :return: str
        """
        raise NotImplementedError("name method is not implemented")

    def get_IPv4s(self):
        """
        Return all knwon IPv4 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        raise NotImplementedError("get_IPv4s method is not implemented")

    def get_IPv6s(self):
        """
        Return all knwon IPv6 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        raise NotImplementedError("get_IPv6s method is not implemented")

    def get_ports(self):
        """
        get ports specified in container metadata

        :return: list of int
        """
        raise NotImplementedError("get_ports method is not implemented")

    def open_connection(self, port=None):
        """
        open a TCP connection to service running in the container, if port is None and
        container exposes only a single port, connect to it, otherwise raise an exception

        :param port: int or None
        :return: list of int
        """
        raise NotImplementedError("open_connection method is not implemented")

    @classmethod
    def run_via_binary(cls, image, args_builder):
        """
        create container using provided image and run it in the background; this method is useful
        to test real user scenarios when users invoke containers using binary and not an API

        :param image: instance of Image
        :param args_builder: instance of BinaryArgsBuilder
        :return: instance of Container
        """
        raise NotImplementedError("run_via_binary method is not implemented")

    @classmethod
    def run_via_api(cls, image, container_params):
        """
        create container using provided image and run it in the background

        :param image: instance of Image
        :param container_params: instance of ContainerParameters
        :return: instance of Container
        """
        raise NotImplementedError("run_via_api method is not implemented")

    @classmethod
    def create(cls, image, container_params):
        """
        create container using provided image

        :param image: instance of Image
        :param container_params: instance of ContainerParameters
        :return: instance of Container
        """
        raise NotImplementedError("create method is not implemented")

    def start(self):
        """
        start current container
        :return: None
        """
        raise NotImplementedError("start method is not implemented")

    def exec(self, command, **kwargs):
        """
        TODO: what about parameters?

        :param command: command to execute in the container
        :param kwargs:
        :return: ? we need to provide output, exit code and there needs to be a possiblity for
                  this thing to be async and blocking
        """
        raise NotImplementedError("exec method is not implemented")

    def logs(self, follow=False):
        """
        get logs from this container

        :param follow: bool, provide iterator if True
        :return: str or iterator
        """
        raise NotImplementedError("logs method is not implemented")

    def stop(self):
        """
        stop this container

        :return: None
        """
        raise NotImplementedError("stop method is not implemented")

    def kill(self, signal=None):
        """
        kill this container

        :param signal: str, signal to use for killing the container
        :return: None
        """
        raise NotImplementedError("kill method is not implemented")

    def rm(self, force=False, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters

        :param force: bool, if container engine supports this, force the functionality
        :return: None
        """
        raise NotImplementedError("rm method is not implemented")

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        raise NotImplementedError("copy_to method is not implemented")

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container to host system

        :param src: str, path to a file or a directory within container
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        raise NotImplementedError("copy_from method is not implemented")

    def get_file(self, file_path):
        """
        provide File object specified via 'file_path'

        :param file_path: str, path to the file
        :return: File instance
        """
        raise NotImplementedError("get_file method is not implemented")


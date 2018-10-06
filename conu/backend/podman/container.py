"""
Implementation of a podman container
"""
from __future__ import print_function, unicode_literals

import logging

from podman import ContainerNotFound

from conu.apidefs.container import Container
from conu.apidefs.metadata import ContainerMetadata
from conu.backend.podman.client import get_client
from conu.exceptions import ConuException

from conu.backend.docker.container import DockerRunBuilder
from conu.utils import run_cmd

from conu.backend.docker.constants import CONU_ARTIFACT_TAG


logger = logging.getLogger(__name__)


class PodmanRunBuilder(DockerRunBuilder):
    """
    helper to execute `podman run` -- users can easily change or override anything
    """

    def __init__(self, command=None, additional_opts=None):
        """
        Build `podman run` command

        :param command: list of str, command to run in the container, examples:
            - ["ls", "/"]
            - ["bash", "-c", "ls / | grep bin"]
        :param additional_opts: list of str, additional options for `podman run`
        """
        super(PodmanRunBuilder, self).__init__(command=command, additional_opts=additional_opts)
        self.binary = ["podman"]

    def build(self):
        return self.binary + self.global_options + self.command + self.options + \
            [self.image_name] + self.arguments
        # FIXME: add ["--label", CONU_ARTIFACT_TAG], now label assignation doesn't work for some reason

    def get_parameters(self):
        raise NotImplementedError("method is not implemented")


class PodmanContainer(Container):
    def __init__(self, image, container_id, name=None, popen_instance=None):
        """
        :param image: PodmanImage instance (if None, it will be found from the container itself)
        :param container_id: str, unique identifier of this container
        :param name: str, pretty container name
        :param popen_instance: instance of Popen
        """
        self.d = get_client()
        super(PodmanContainer, self).__init__(image, container_id, name)
        self.popen_instance = popen_instance
        self._inspect_data = None
        self.metadata = ContainerMetadata()

    def __repr__(self):
        return "PodmanContainer(image=%s, id=%s)" % (self.image, self.get_id())

    def __str__(self):
        return self.get_id()

    def get_id(self):
        """
        get unique identifier of this container

        :return: str
        """
        if self._id is None:
            # FIXME: provide a better error message when key is not defined
            self._id = self.inspect(refresh=False)["id"]
        return self._id

    def inspect(self, refresh=True):
        """
        return cached metadata by default

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        if refresh or not self._inspect_data:
            ident = self._id or self.name
            if not ident:
                raise ConuException("This container does not have a valid identifier.")
            self._inspect_data = self.d.containers.get(ident).inspect()
            # FIXME: get rid of protected method _asdict()
            self._inspect_data = dict(self._inspect_data._asdict())
        return self._inspect_data

    def is_running(self):
        """
        returns True if the container is running

        :return: bool
        """
        try:
            return self.inspect(refresh=True)["state"]["running"]
        except ContainerNotFound:
            return False

    def delete(self, force=False, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters

        :param force: bool, if container engine supports this, force the functionality
        :return: None
        """
        # TODO: Implement volumes removing
        # :param volumes: bool, remove also associated volumes
        self.d.containers.get(self.get_id()).remove(force=force)

    def mount(self, mount_point=None):
        """
        mount container filesystem

        :return: str, the location of the mounted file system
        """
        # TODO: implement mount point
        cmd = ["podman", "mount", self.get_id()]
        output = run_cmd(cmd, return_output=True).rstrip("\n\r")
        return output

    def umount(self, all=False, force=True):
        """
        unmount container filesystem
        :param all: bool, option to unmount all mounted containers
        :param force: bool, force the unmounting of specified containers' root file system
        :return: str, the output from cmd
        """
        # FIXME: handle error if unmount didn't work
        options = []
        if force: options.append('--force')
        if all: options.append('--all')
        cmd = ["podman", "umount"] + options + [self.get_id() if not all else ""]
        return run_cmd(cmd, return_output=True)

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        # logger.debug("copying %s from host to container at %s using 'podman mount'", src, dest)
        # full_dest = self.mount() + dest
        # cmd = ["cp", "-R", src, full_dest]
        # run_cmd(cmd)
        raise NotImplementedError("method is not implemented")

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container or image to host system.

        :param src: str, path to a file or a directory within container or image
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        # using `podman cp` b/c get_archive is too complicated
        # logger.debug("copying %s from host to container at %s", src, dest)
        # cmd = ["podman", "cp", "%s:%s" % (self.get_id(), src), dest]
        # run_cmd(cmd)
        raise NotImplementedError("method is not implemented")

    def execute(self, command, blocking=True):
        """
        Execute a command in this container -- the container needs to be running.

        :param command: list of str, command to execute in the container
        :param blocking: bool, if True blocks until the command finishes
        :return: iterator if non-blocking or list of bytes if blocking
        """
        # FIXME: there is no exec method in podman python API so use cmd
        logger.info("running command %s", command)
        # podman exec container [options] [command [arg ...]]
        cmd = ["podman", "exec"] + [self.get_id()] + command
        output = run_cmd(cmd, return_output=True)
        if blocking:
            response = []
            for line in output:
                response.append(line)
                logger.info("%s", line.decode("utf-8").strip("\n\r"))
            return response
        return output

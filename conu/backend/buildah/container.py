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
Implementation of a podman container
"""
from __future__ import print_function, unicode_literals

import json
import logging

from conu import DockerRunBuilder
from conu.apidefs.container import Container
from conu.apidefs.metadata import ContainerMetadata
from conu.backend.buildah.utils import buildah_common_inspect_to_metadata
from conu.exceptions import ConuException
from conu.utils import run_cmd, graceful_get, parse_reference

logger = logging.getLogger(__name__)


class BuildahRunBuilder(DockerRunBuilder):
    """
    helper to execute `buildah from` -- users can easily change or override anything
    """

    def __init__(self, command=None, additional_opts=None):
        """
        Build `buildah from` command

        :param command: ignored, please use the exec() method
        :param additional_opts: list of str, additional options for `buildah from`
        """
        if command:
            logger.warning("command argument is ignored for buildah, please use exec()")
        super(BuildahRunBuilder, self).__init__(additional_opts=additional_opts)
        self.binary = ["buildah"]
        self.command = ["from"]

    def build(self):
        return self.binary + self.global_options + self.command + self.options + [self.image_name]

    def get_parameters(self):
        raise NotImplementedError("method is not implemented")


def buildah_container_inspect_to_metadata(inspect_data):
    """
    process data from `buildah inspect -t container` and return ContainerMetadata

    :param inspect_data: dict, metadata from `buildah inspect -t container`
    :return: instance of ContainerMetadata
    """
    cm = ContainerMetadata()
    cm.name = graceful_get(inspect_data, 'Container')
    cm.identifier = graceful_get(inspect_data, 'ContainerID')
    buildah_common_inspect_to_metadata(cm, inspect_data)
    return cm


class BuildahContainer(Container):
    def __init__(self, image, container_id, name=None, popen_instance=None, image_class=None):
        """
        :param image: BuildahImage instance (if None, it will be found from the container itself)
        :param container_id: str, unique identifier of this container
        :param name: str, pretty container name
        :param popen_instance: instance of Popen
        """
        super(BuildahContainer, self).__init__(image, container_id, name)
        self.popen_instance = popen_instance
        self._inspect_data = None
        self._metadata = None
        self.ImageClass = image.__class__ if image else image_class

    def __repr__(self):
        return "BuildahContainer(image=%s, id=%s)" % (self.image, self.get_id())

    def __str__(self):
        return self.get_id()

    def get_id(self):
        """
        get unique identifier of this container

        :return: str
        """
        if self._id is None:
            self._id = graceful_get(self.inspect(refresh=False), "ContainerID")
        return self._id

    def get_name(self):
        """
        Returns name of the container

        :return: str
        """
        self.name = self.name or graceful_get(self.inspect(refresh=False), "Container")
        return self.name

    def inspect(self, refresh=True):
        """
        provide metadata about the buildah container

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        if refresh or not self._inspect_data:
            identifier = self._id or self.name
            if not identifier:
                raise ConuException("This container does not have a valid identifier.")
            self._inspect_data = self._inspect(identifier)
        return self._inspect_data

    @staticmethod
    def _inspect(identifier):
        cmdline = ["buildah", "inspect", "--type", "container", identifier]
        output = run_cmd(cmdline, return_output=True, log_output=False)
        return json.loads(output)

    def is_running(self):
        """
        buildah containers are always running if they exist

        :return: True
        """
        return True

    def get_IPv4s(self):
        """
        buildah containers don't have this concept of a running service
        """
        raise ConuException("This method is intentionally not implemented for Buildah containers.")

    def get_IPv6s(self):
        """
        buildah containers don't have this concept of a running service
        """
        raise ConuException("This method is intentionally not implemented for Buildah containers.")

    def get_ports(self):
        """
        buildah containers don't have this concept of a running service
        """
        raise ConuException("This method is intentionally not implemented for Buildah containers.")

    def is_port_open(self, port, timeout=2):
        """
        buildah containers don't have this concept of a running service
        """
        raise ConuException("This method is intentionally not implemented for Buildah containers.")

    def get_port_mappings(self, port=None):
        """
        buildah containers don't have this concept of a running service
        """
        raise ConuException("This method is intentionally not implemented for Buildah containers.")

    def get_image_name(self):
        """
        return name of the container image

        :return: str
        """
        return graceful_get(self.inspect(refresh=False), "FromImage")

    def wait_for_port(self, port, timeout=10, **probe_kwargs):
        """
        buildah containers don't have this concept of a running service
        """
        raise ConuException("This method is intentionally not implemented for Buildah containers.")

    def delete(self, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters
        """
        cmdline = ["buildah", "rm", self.get_name()]
        run_cmd(cmdline)

    def mount(self, mount_point=None):
        """
        mount container filesystem

        :return: str, the location of the mounted file system
        """
        # TODO: In rootless mode you must use buildah unshare first.
        cmd = ["buildah", "mount", self._id or self.get_id()]
        output = run_cmd(cmd, return_output=True).rstrip("\n\r")
        return output

    def umount(self, all=False):
        """
        unmount container filesystem

        :param all: bool, option to unmount all mounted containers
        :return: str, the output from cmd
        """
        options = []
        if all:
            options.append('--all')
        cmd = ["buildah", "umount"] + options
        if not all:
            cmd += [self.get_id()]
        return run_cmd(cmd, return_output=True)

    def logs(self, follow=False):
        """
        Get logs from this container. Iterator has one log line followed by a newline in next item.
        The logs are NOT encoded (they are str, not bytes).

        Let's look at an example::

            image = conu.BuildahImage("fedora", tag="27")
            command = ["bash", "-c", "for x in `seq 1 5`; do echo $x; sleep 1; done"]
            container = image.run_via_binary(command=command)
            for line in container.logs(follow=True):
                print(line)

        This will output

        .. code-block:: none

            '1' '\n' '2' '\n' '3' '\n' '4' '\n' '5' '\n'

        :param follow: bool, provide new logs as they come
        :return: iterator (of str)
        """
        # TODO: podman logs have different behavior than docker
        follow = ["--follow"] if follow else []
        cmdline = ["podman", "logs"] + follow + [self._id or self.get_id()]
        output = run_cmd(cmdline, return_output=True)
        return output

    def get_status(self):
        """
        Get status of container

        :return: one of: 'created', 'restarting', 'running', 'paused', 'exited', 'dead'
        """
        return graceful_get(self.inspect(refresh=True), "State", "Status")

    def wait(self, timeout=None):
        """
        Block until the container stops, then return its exit code. Similar to
        the ``podman wait`` command.

        :param timeout: int, microseconds to wait before polling for completion
        :return: int, exit code
        """
        timeout = ["--interval=%s" % timeout] if timeout else []
        cmdline = ["podman", "wait"] + timeout + [self._id or self.get_id()]
        return run_cmd(cmdline, return_output=True)

    def exit_code(self):
        """
        get exit code of container. Return value is 0 for running and created containers

        :return: int
        """
        return graceful_get(self.inspect(refresh=True), "State", "ExitCode")

    def execute(self, command, options=None, **kwargs):
        """
        Execute a command in this container

        :param command: list of str, command to execute in the container
        :param options: list of str, additional options to run command
        :return: str
        """
        options = options or []
        logger.info("running command %s", command)
        cmd = ["buildah", "run"] + options + [self.get_id()] + command
        output = run_cmd(cmd, return_output=True)
        return output

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self.get_metadata()
        return self._metadata

    def get_metadata(self):
        """
        Convert dictionary returned after podman inspect command into instance of ContainerMetadata class
        :return: ContainerMetadata, container metadata instance
        """
        if self._metadata is None:
            inspect_data = self.inspect(refresh=True)
            self._metadata = buildah_container_inspect_to_metadata(inspect_data)

            # this is a hack to avoid circular imports: feel free to fix it
            if self.ImageClass:
                image_id = graceful_get(inspect_data, "FromImageID")
                image_name = graceful_get(inspect_data, "FromImage")
                if image_name:
                    image_repo, tag = parse_reference(image_name)
                else:
                    image_repo, tag = None, None
                self._metadata.image = self.ImageClass(image_repo, tag=tag, identifier=image_id)
        return self._metadata

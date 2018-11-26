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

import functools
import logging
import json
import subprocess

from conu.apidefs.container import Container
from conu.apidefs.metadata import ContainerMetadata
from conu.exceptions import ConuException

from conu.backend.docker.container import DockerRunBuilder
from conu.backend.podman.utils import inspect_to_container_metadata

from conu.utils import check_port, run_cmd, graceful_get
from conu.utils.probes import Probe

from conu.backend.podman.constants import CONU_ARTIFACT_TAG


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
               ["--label", "%s=1" % CONU_ARTIFACT_TAG] + [self.image_name] + self.arguments

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
        super(PodmanContainer, self).__init__(image, container_id, name)
        self.popen_instance = popen_instance
        self._inspect_data = None
        self._metadata = None

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
            self._id = graceful_get(self.inspect(refresh=True), "ID")
        return self._id

    def get_name(self):
        """
        Returns name of the container
        :return: str
        """
        self.name = self.name or graceful_get(self.inspect(refresh=False), "Name")
        return self.name

    def inspect(self, refresh=True):
        """
        return cached metadata by default

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
        cmdline = ["podman", "container", "inspect", identifier]
        output = run_cmd(cmdline, return_output=True, log_output=False)
        return json.loads(output)[0]

    def is_running(self):
        """
        returns True if the container is running

        :return: bool
        """
        try:
            return graceful_get(self.inspect(refresh=True), "State", "Running")
        except subprocess.CalledProcessError:
            return False

    def get_IPv4s(self):
        """
        Return all known IPv4 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        self.get_metadata()  # force update of metadata, we should probably do this better
        return self.metadata.ipv4_addresses

    def get_IPv6s(self):
        """
        Return all known IPv6 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        self.get_metadata()  # force update of metadata, we should probably do this better
        return self.metadata.ipv6_addresses

    def get_ports(self):
        """
        get ports specified in container metadata

        :return: list of str
        """
        ports = []
        container_ports = graceful_get(self.inspect(refresh=True), "NetworkSettings", "Ports")
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
        port_mappings = graceful_get(self.inspect(refresh=True), "NetworkSettings", "Ports")

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

    def delete(self, force=False, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters

        :param force: bool, if container engine supports this, force the functionality
        :return: None
        """
        cmdline = ["podman", "rm", "--force" if force else "", self.get_name()]
        run_cmd(cmdline)

    def mount(self, mount_point=None):
        """
        mount container filesystem

        :return: str, the location of the mounted file system
        """
        cmd = ["podman", "mount", self._id or self.get_id()]
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
        if force:
            options.append('--force')
        if all:
            options.append('--all')
        cmd = ["podman", "umount"] + options + [self.get_id() if not all else ""]
        return run_cmd(cmd, return_output=True)

    def logs(self, follow=False):
        """
        Get logs from this container. Iterator has one log line followed by a newline in next item.
        The logs are NOT encoded (they are str, not bytes).

        Let's look at an example::

            image = conu.PodmanImage("fedora", tag="27")
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

    def execute(self, command):
        """
        Execute a command in this container -- the container needs to be running.

        :param command: list of str, command to execute in the container
        :return: str
        """

        logger.info("running command %s", command)
        cmd = ["podman", "exec", self.get_id()] + command
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
            self._metadata = ContainerMetadata()
        inspect_to_container_metadata(self._metadata, self.inspect(refresh=True), self.image)
        return self._metadata

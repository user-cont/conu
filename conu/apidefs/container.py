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
Abstract class definitions for containers.
"""
from __future__ import print_function, unicode_literals

from conu.apidefs.image import Image
from conu.utils.http_client import HttpClient, get_url

import requests
from six.moves.urllib.parse import urlunsplit
from contextlib import contextmanager


class Container(object):
    """
    Container class definition which contains abstract methods. The instances should call the
    constructor
    """
    def __init__(self, image, container_id, name):
        """
        :param image: Image instance
        :param container_id: str, unique identifier of this container
        :param container_id: str, pretty container name
        """
        self.name = name
        self._id = container_id

        if not image:
            image_name = self.get_image_name()
            if image_name:
                image = Image(image_name)

        elif not isinstance(image, Image):
            raise RuntimeError("image argument is not an instance of Image class")
        self.image = image
        self._metadata = None

        # provides HTTP client (requests.Session)
        self.http_session = requests.Session()

    def http_request(self, path="/", method="GET", host=None, port=None, json=False, data=None):
        """
        perform a HTTP request

        :param path: str, path within the reqest, e.g. "/api/version"
        :param method: str, HTTP method
        :param host: str, if None, set self.get_IPv4s()[0]
        :param port: str or int, if None, set to self.get_ports()[0]
        :param json: bool, should we expect json?
        :param data: data to send (can be dict, list, str)
        :return: dict
        """
        host = host or self.get_IPv4s()[0]
        port = port or self.get_ports()[0]
        url = get_url(host=host, port=port, path=path)

        return self.http_session.request(method, url, json=json, data=data)

    @contextmanager
    def http_client(self, host=None, port=None):
        """
        allow requests in context -- e.g.:

        .. code-block:: python

            with container.http_client(port="80", ...) as c:
                assert c.get("/api/...")


        :param host: str, if None, set self.get_IPv4s()[0]
        :param port: str or int, if None, set to self.get_ports()[0]
        :return: instance of :class:`conu.utils.http_client.HttpClient`
        """

        host = host or self.get_IPv4s()[0]
        port = port or self.get_ports()[0]

        yield HttpClient(host, port, self.http_session)

    def get_id(self):
        """
        get unique identifier of this container

        :return: str
        """
        raise NotImplementedError("get_id method is not implemented")

    def inspect(self, refresh=False):
        """
        return cached metadata by default

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        raise NotImplementedError("inspect method is not implemented")

    def get_metadata(self):
        """
        return general metadata for container

        :return: ContainerMetadata
        """

        raise NotImplementedError("get_metadata method is not implemented")

    def get_image_name(self):
        """
        return name of the container image

        :return: str
        """
        raise NotImplementedError("get_image_name method is not implemented")

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
        Return all known IPv4 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        raise NotImplementedError("get_IPv4s method is not implemented")

    def get_IPv6s(self):
        """
        Return all known IPv6 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        raise NotImplementedError("get_IPv6s method is not implemented")

    def get_ports(self):
        """
        get ports specified in container metadata

        :return: list of str
        """
        raise NotImplementedError("get_ports method is not implemented")

    def is_port_open(self, port, timeout=10):
        """
        check if given port is open and receiving connections

        :param port: int
        :param timeout: int, how many seconds to wait for connection; defaults to 2
        :return: True if the connection has been established inside timeout, False otherwise
        """
        raise NotImplementedError("is_port_open method is not implemented")

    def open_connection(self, port=None):
        """
        open a TCP connection to service running in the container, if port is None and
        container exposes only a single port, connect to it, otherwise raise an exception

        :param port: int or None
        :return: socket
        """
        raise NotImplementedError("open_connection method is not implemented")

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

        :param src: str, path to a file or a directory within container or image
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        raise NotImplementedError("copy_from method is not implemented")

    def start(self):
        """
        start current container - the container has to be created

        :return: None
        """
        raise NotImplementedError("start method is not implemented")

    # exec is a keyword in python
    def execute(self, command, **kwargs):
        """
        execute a command in this container

        :param command: list of str, command to execute in the container
        :param kwargs: specific parameters for container engines exec methods
        :return: str (output) or iterator
        """
        raise NotImplementedError("execute method is not implemented")

    def logs(self, follow=False):
        """
        Get logs from this container.

        :param follow: bool, provide new logs as they come
        :return: iterator
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
        send a signal to this container (bear in mind that the process won't have time
        to shutdown properly and your service may end up in an inconsistent state)

        :param signal: str or int, signal to use for killing the container (SIGKILL by default)
        :return: None
        """
        raise NotImplementedError("kill method is not implemented")

    def delete(self, force=False, **kwargs):
        """
        remove this container; kwargs indicate that some container runtimes
        might accept more parameters

        :param force: bool, if container engine supports this, force the functionality
        :return: None
        """
        raise NotImplementedError("rm method is not implemented")

    def mount(self, mount_point=None):
        """
        mount container filesystem

        :param mount_point: str, directory where the filesystem will be mounted
        :return: instance of Filesystem
        """
        raise NotImplementedError("mount is not implemented")

    def get_status(self):
        """
        Get status of container

        :return: Status of container
        """
        raise NotImplementedError("get_status is not implemented")

    def wait(self, timeout):
        """
        Block until the container stops, then return its exit code.

        :param timeout: int, Request timeout
        :return: int, exit code
        """
        raise NotImplementedError("wait is not implemented")

    def exit_code(self):
        """
        get exit code of container. Return value is 0 for running and created containers

        :return: int
        """
        raise NotImplementedError("exit_code is not implemented")

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
Implementation of a fake container. Runs commands on localhost
"""

import logging
import subprocess
import time
import json

from conu.apidefs.container import Container
from conu.utils import run_cmd, convert_kv_to_dict


logger = logging.getLogger(__name__)


class NullContainer(Container):

    def __init__(self, image, container_id, name=None,
                 popen_instance=None, start_process=None, start_action=None):
        """
        Utilities usable for containers

        :param image: image to use (instance of Image class)
        :param container_id: id of running container (created by Image.run method)
        :param name: optional name of container
        :param popen_instance: not used anyhow now
        :param start_process: subporocess instance with start process
        :param start_action: set with 4 parameters for starting container
        """
        super(NullContainer, self).__init__(image, container_id, name)
        if not name:
            self.name = self._id
        self.popen_instance = popen_instance
        self.start_process = start_process
        self.start_action = start_action

    def __repr__(self):
        # TODO: very similar to Docker method, move to API, this is the proper
        # way
        return "%s(image=%s, id=%s)" % (
            self.__class__, self.image, self.get_id())

    def __str__(self):
        # TODO: move to API
        return self.get_id()

    def start(self):
        self.start_process = NullContainer.internal_run_container(name=self.name, callback_method=self.start_action)
        return self.start_process

    def get_id(self):
        """
        get identifier of container
        :return: str
        """
        return self._id

    def inspect(self, refresh=True):
        """
        return cached metadata by default (a convenience method)

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        # TODO: move to API defs
        return self.get_metadata(refresh=refresh)

    def get_metadata(self, refresh=True):
        """
        return cached metadata by default

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        if refresh or not self._metadata:
            try:
                output = run_cmd(["machinectl", "show", ".host"], return_output=True)
                self._metadata = convert_kv_to_dict(output)
            except subprocess.CalledProcessError:
                output = run_cmd(["lshw", "-json"], return_output=True)
                self._metadata = json.loads(output)
        return self._metadata

    def is_running(self):
        """
        return bool in case container is running

        :return: bool
        """
        return self.start_process.poll() is None

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["cp", src, dest]
        run_cmd(cmd)

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container or image to host system.

        :param src: str, path to a file or a directory within container or image
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["cp", src, dest]
        run_cmd(cmd)

    def stop(self):
        """
        stop this  process container

        :return: None
        """
        self.start_process.kill()
        # give kernel 1 sec to terminate process and do async ops
        time.sleep(1)

    def kill(self, signal=None):
        """
        terminate process container

        :param signal: Not used
        :return:
        """
        self.start_process.terminate()
        # give kernel 1 sec to terminate process and do async ops
        time.sleep(1)

    def execute(
            self, command, *args, **kwargs):
        """
        execute command via systemd-run inside container

        :param command: command to run inside
        :param args: pass params to subprocess
        :param kwargs: pass params to subprocess
        :return: subprocess object
        """

        return subprocess.Popen(command, *args, **kwargs)

    def selfcheck(self):
        """
        It is true, because host is running

        :return: bool
        """

        return True

    def mount(self, mount_point=None):
        """
        mount filesystem inside, container (image)

        :param mount_point: str, where to mount
        :return: NspawnImageFS instance
        """
        return self.image.mount(mount_point=mount_point)

    @staticmethod
    def internal_run_container(name, callback_method, foreground=False):
        """
        Internal method what runs container process

        :param name: str - name of container
        :param callback_method: list - how to invoke container
        :param foreground: bool run in background by default
        :return: suprocess instance
        """
        if callback_method[1]:
            logger.info("Stating machine (command) {}".format(name))
            container_process = callback_method[0](callback_method[1], *callback_method[2], **callback_method[3])
            if foreground:
                pass
                #logger.info("wait for command is finished" % name)
                #container_process.communicate()
            logger.info("machine: %s starting finished" % name)
            return container_process


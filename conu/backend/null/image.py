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
Utilities related to manipulate nspawn images.
"""

import logging
import subprocess
from copy import deepcopy

from container import NullContainer
from conu.apidefs.filesystem import Filesystem
from conu.apidefs.image import Image
from conu.utils import run_cmd

logger = logging.getLogger(__name__)


class NullImageFS(Filesystem):

    def __init__(self, image, mount_point=None):
        """
        Raises CommandDoesNotExistException if the command is not present on the system.

        :param image: instance of NspawnImage
        :param mount_point: str, directory where the filesystem will be mounted
        """
        self.mount_point_exists = False
        super(NullImageFS, self).__init__(image, mount_point=mount_point)
        self.image = image


class NullImage(Image):
    """
    Utility functions for work with base system) null copntainer.
    """
    special_separator = "_"

    def __init__(self, repository="", tag=""):
        """
        :param repository: not used
        :param tag: not used
        """

        self.container_process = None

        super(NullImage, self).__init__(repository, tag=tag)

    def __repr__(self):
        return "NullImage(repository=%s, tag=%s)" % (self.name, self.tag)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Provide full, complete image name

        :return: str
        """
        return " ".join([self.name, self.tag])

    def get_id(self):
        """
        get unique identifier of this image

        :return: str
        """

        if self._id is None:
            self._id = run_cmd(["uname", "-a"], return_output=True).split("\n")[0].strip()
        return self._id

    def is_present(self):
        """
        Check if image is already imported in images

        :return: bool
        """
        return True

    def pull(self):
        """
        Pull this image from URL. Raises an exception if the image is not found in
        the registry.

        :return: None
        """
        pass


    def inspect(self, refresh=True):
        """
        return cached metadata by default (a convenience method)

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        # TODO: move to API it is same
        return self.get_metadata(refresh=refresh)

    def get_metadata(self, refresh=True):
        """
        return cached metadata by default

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        output = {}
        if refresh or not self._metadata:
            whole_output = run_cmd(["mount", "-v"], return_output=True)
            for line in whole_output.split("\n"):
                stripped = line.strip()
                if stripped:
                    what, notused, where, notused, fstype, opts = line.split(" ", 6)
                    output[where] = [what, fstype, opts]
            self._metadata = output
        return self._metadata

    def mount(self, mount_point=None):
        """
        mount image filesystem

        :param mount_point: str, directory where the filesystem will be mounted
        :return: instance of NspawnImageFS
        """
        return NullImageFS(self, mount_point=mount_point)

    def run(self, command=None, foreground=False, *args, **kwargs):
        command = deepcopy(command) or []
        machine_name = " ".join(command)
        callback_method = (subprocess.Popen, command, args, kwargs)
        self.container_process = NullContainer.internal_run_container(name=machine_name,
                                                                      callback_method=callback_method,
                                                                      foreground=foreground)
        if foreground:
            return self.container_process
        else:
            return NullContainer(self, container_id=machine_name,
                                 start_process=self.container_process, start_action=callback_method)

    def run_foreground(self, *args, **kwargs):
        """
        Force to run process at foreground
        :param args: pass args to run command
        :param kwargs: pass args to run command
        :return:  process or NullContianer instance
        """
        return self.run(foreground=True, *args, **kwargs)

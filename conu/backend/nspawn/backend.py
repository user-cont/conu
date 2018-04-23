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
This is backend for nspawn engine
"""
import logging
import re
import subprocess

from conu.apidefs.backend import Backend
from conu.backend.nspawn.container import NspawnContainer
from conu.backend.nspawn.image import NspawnImage, ImagePullPolicy
from conu.backend.nspawn.constants import CONU_ARTIFACT_TAG
from conu.utils import run_cmd


logger = logging.getLogger(__name__)


class NspawnBackend(Backend):
    """
    For more info on using the Backend classes, see documentation of
    the parent :class:`conu.apidefs.backend.Backend` class.
    """
    name = "nspawn"
    ImageClass = NspawnImage
    ContainerClass = NspawnContainer

    def list_containers(self):
        """
        list all available nspawn containers

        :return: collection of instances of :class:`conu.backend.nspawn.container.NspawnContainer`
        """
        data = run_cmd(["machinectl", "list", "--no-legend", "--no-pager"],
                       return_output=True)
        output = []
        reg = re.compile(r"\s+")
        for line in data.split("\n"):
            stripped = line.strip()
            if stripped:
                parts = reg.split(stripped)
                name = parts[0]
                output.append(self.ContainerClass(None, None, name=name))
        return output

    def list_images(self):
        """
        list all available nspawn images

        :return: collection of instances of :class:`conu.backend.nspawn.image.NspawnImage`
        """
        # Fedora-Cloud-Base-27-1.6.x86_64 raw  no  601.7M Sun 2017-11-05 08:30:10 CET \
        #   Sun 2017-11-05 08:30:10 CET
        data = run_cmd(["machinectl", "list-images", "--no-legend", "--no-pager"],
                       return_output=True)
        output = []
        reg = re.compile(r"\s+")
        for line in data.split("\n"):
            stripped = line.strip()
            if stripped:
                parts = reg.split(stripped)
                name = parts[0]
                output.append(self.ImageClass(name, pull_policy=ImagePullPolicy.NEVER))
        return output

    def cleanup_containers(self):
        """
        stop all container created by conu

        :return: None
        """
        for cont in self.list_containers():
            if CONU_ARTIFACT_TAG in cont.name:
                try:
                    logger.debug("removing container %s created by conu", cont)
                    # TODO: move this functionality to container.delete
                    run_cmd(["machinectl", "terminate", cont])
                except subprocess.CalledProcessError as e:
                    logger.error("unable to remove container %s: %r", cont, e)

    def cleanup_images(self):
        """
        Remove all images created by CONU and remove all hidden images (cached dowloads)

        :return: None
        """
        for image in self.list_images():
            if CONU_ARTIFACT_TAG in image.name:
                image.rmi()
        # remove all hidden images -> causes trouble when pulling the image again
        run_cmd(["machinectl", "--no-pager", "clean"])

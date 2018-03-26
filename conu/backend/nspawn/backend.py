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

from conu.apidefs.backend import Backend
from conu.backend.nspawn.image import NspawnImage
from conu.backend.nspawn.container import NspawnContainer
from conu.utils import run_cmd


logger = logging.getLogger(__name__)


# let this class inherit docstring from its parent
class NspawnBackend(Backend):
    """
    For more info on using the Backend classes, see documentation of
    the parent :class:`conu.apidefs.backend.Backend` class.
    """
    ImageClass = NspawnImage
    ContainerClass = NspawnContainer

    def list_containers(self):
        """
        list all available nspawn containers

        :return: collection of instances of :class:`conu.backend.nspawn.container.NspawnContainer`
        """
        data = run_cmd(["machinectl", "list"], return_output=True)
        output = []
        for line in data.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(
                    "MACHINE") or "No machines" in line or "machines listed" in line:
                continue
            if " systemd-nspawn " in line and constants.CONU_ARTIFACT_TAG in line:
                output.append(stripped.split(" ", 1))
        return output

    def list_images(self):
        """
        list all available nspawn images

        :return: collection of instances of :class:`conu.backend.nspawn.image.NspawnImage`
        """
        # images tagged with ARTIFACT TAG
        data = run_cmd(["machinectl", "list-images"], return_output=True)
        output = []
        for line in data.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(
                    "NAME") or "No images" in line or "images listed" in line:
                continue
            splitted = stripped.split(" ", 1)
            if "raw" in splitted[
                1] and constants.CONU_ARTIFACT_TAG in splitted[0]:
                output.append(splitted[0])
        return output

    def cleanup_containers(self):
        """
        stop all container created by conu

        :return: None
        """
        for cont in NspawnContainer.list_all():
            try:
                logger.debug("Removing container %s created by conu", cont)
                # TODO: find way, how to initialize image for container to use
                # there container.stop() method
                run_cmd(["machinectl", "terminate", cont])
            except Exception as e:
                logger.error("unable to remove container %s: %r", cont, e)

    def cleanup_images(self):
        """
        Remove all images created by CONU and remove all hidden images (cached dowloads)

        :return: None
        """
        for imname in NspawnImage.list_all():
            im = NspawnImage(repository=imname)
            im.rmi()
        # remove all hidden images -> causes troubles when pull image again
        run_cmd(["machinectl", "clean"])

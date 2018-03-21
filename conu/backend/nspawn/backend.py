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
from container import NspawnContainer
from image import NspawnImage
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

    @staticmethod
    def cleanup_containers():
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
                logger.log("unable to remove container: {}".format(cont))

    @staticmethod
    def cleanup_images():
        """
        Remove all images created by CONU and remove all hidden images (cached dowloads)

        :return: None
        """
        for imname in NspawnImage.list_all():
            im = NspawnImage(repository=imname)
            im.rmi()
        # remove all hidden images -> causes troubles when pull image again
        run_cmd(["machinectl", "clean"])

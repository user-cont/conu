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
This is backend for buildah
"""
import json
import logging
import re

from conu.apidefs.backend import Backend
from conu.backend.buildah.container import BuildahContainer
from conu.backend.buildah.image import BuildahImage, BuildahImagePullPolicy
from conu.utils import run_cmd, parse_reference


logger = logging.getLogger(__name__)


class BuildahBackend(Backend):
    """
    For more info on using the Backend classes, see documentation of
    the parent :class:`conu.apidefs.backend.Backend` class.
    """
    name = "buildah"
    ContainerClass = BuildahContainer
    ImageClass = BuildahImage

    def __init__(self, logging_level=logging.INFO, logging_kwargs=None, cleanup=None):
        """
        This method serves as a configuration interface for conu.

        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        :param cleanup: unsupported
        """
        if cleanup:
            logger.warning("cleanup is not supported by the buildah backend")
        super(BuildahBackend, self).__init__(
            logging_level=logging_level, logging_kwargs=logging_kwargs, cleanup=cleanup)

    def get_version(self):
        """
        return 3-tuple of version info or None

        :return: (str, str, str)
        """
        raw_version = run_cmd(["buildah", "version"], return_output=True)
        regex = re.compile(r"Version:\s*(\d+)\.(\d+)\.(\d+)")
        match = regex.findall(raw_version)
        try:
            return match[0]
        except IndexError:
            logger.error("unable to parse version from `buildah version`")
            return

    def list_containers(self):
        """
        List all available buildah containers.

        :return: collection of instances of :class:`conu.BuildahContainer`
        """
        containers = []
        for container in self._list_buildah_containers():
            identifier = container["id"]
            container_name = container["containername"]
            image_id = container["imageid"]
            image_name = container["imagename"]
            image = BuildahImage(image_name, identifier=image_id)
            container = BuildahContainer(image, container_id=identifier, name=container_name,
                                         image_class=self.ImageClass)
            containers.append(container)
        return containers

    def list_images(self):
        """
        List all available buildah images.

        :return: collection of instances of :class:`conu.BuildahImage`
        """
        images = []
        for image in self._list_all_buildah_images():
            try:
                i_name, tag = parse_reference(image["names"][0])
            except (IndexError, TypeError):
                i_name, tag = None, None
            d_im = BuildahImage(
                i_name, tag=tag, identifier=image["id"],
                pull_policy=BuildahImagePullPolicy.NEVER)
            images.append(d_im)

        return images

    @staticmethod
    def _list_all_buildah_images():
        """
        List all buildah images

        sample image:
        "id": "9754ce14641df7f1f3751d21e14b3037dce7dca2472cf4cdff38d96891703453",
        "names": [
            "docker.io/library/fedora:30"
        ]

        :return: list of dicts with image info
        """
        cmdline = ["buildah", "images", "--json"]
        output = run_cmd(cmdline, return_output=True)
        images = json.loads(output)
        if not images:
            return []
        return images

    @staticmethod
    def _list_buildah_containers(filter=None):
        """
        Enumerate buildah containers using a filter or list all

        sample container:
         {'id': '839e3dc37673530f26277baf1cb839f4f435f6f55cad941ed63c1919417727e4',
          'builder': True,
          'imageid': 'd474c1e8e5bcb9f2a37b8ba30fea895398b3dc926bf5334c3df0b294e9866190',
          'imagename': '',
          'containername': 'd474c1e8e5bcb9f2a37b8ba30fea895398b3dc926bf5334c3df0b294e9866190-working-container'},

        :param filter: filter to use, see `man buildah-containers` for more info
        :return: list of dicts with containers info
        """
        option = ["--filter", filter] if filter else ["-a"]
        cmdline = ["buildah", "ps"] + option + ["--json"]
        output = run_cmd(cmdline, return_output=True)
        containers = json.loads(output)
        if not containers:
            return []
        return containers

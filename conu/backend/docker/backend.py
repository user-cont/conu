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
This is backend for docker engine
"""
import logging

from conu.apidefs.backend import Backend
from conu.backend.docker.container import DockerContainer
from conu.backend.docker.image import DockerImage, DockerImagePullPolicy
from conu.backend.docker.client import get_client
from conu.backend.docker.constants import CONU_ARTIFACT_TAG
from conu.backend.docker.utils import inspect_to_metadata, inspect_to_container_metadata

logger = logging.getLogger(__name__)


def parse_reference(reference):
    """
    parse provided image reference into <image_repository>:<tag>

    :param reference: str, e.g. (registry.fedoraproject.org/fedora:27)
    :return: collection (tuple or list), ("registry.fedoraproject.org/fedora", "27")
    """
    if ":" in reference:
        im, tag = reference.rsplit(":", 1)
        if "/" in tag:
            # this is case when there is port in the registry URI
            return (reference, "latest")
        else:
            return (im, tag)

    else:
        return (reference, "latest")


# let this class inherit docstring from its parent
class DockerBackend(Backend):
    """
    For more info on using the Backend classes, see documentation of
    the parent :class:`conu.apidefs.backend.Backend` class.
    """
    name = "docker"
    ContainerClass = DockerContainer
    ImageClass = DockerImage

    def __init__(self, logging_level=logging.INFO, logging_kwargs=None, cleanup=None):
        """
        This method serves as a configuration interface for conu.

        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        :param cleanup: list, list of cleanup policy values, examples:
            - [CleanupPolicy.EVERYTHING]
            - [CleanupPolicy.VOLUMES, CleanupPolicy.TMP_DIRS]
            - [CleanupPolicy.NOTHING]
        """
        super(DockerBackend, self).__init__(
            logging_level=logging_level, logging_kwargs=logging_kwargs, cleanup=cleanup)
        self.d = get_client()

    def cleanup_containers(self):
        conu_containers = self.d.containers(filters={'label': CONU_ARTIFACT_TAG}, all=True)
        for c in conu_containers:
            id = c['Id']
            logger.debug("Removing container %s created by conu", id)
            self.d.stop(id)
            self.d.remove_container(id)

    def list_containers(self):
        """
        List all available docker containers.

        Container objects returned from this methods will contain a limited
        amount of metadata in property `short_metadata`. These are just a subset
        of `.inspect()`, but don't require an API call against dockerd.

        :return: collection of instances of :class:`conu.DockerContainer`
        """
        result = []
        for c in self.d.containers(all=True):
            name = None
            names = c.get("Names", None)
            if names:
                name = names[0]
            i = DockerImage(None, identifier=c["ImageID"])
            cont = DockerContainer(i, c["Id"], name=name)
            # TODO: docker_client.containers produces different metadata than inspect
            inspect_to_container_metadata(cont.metadata, c, i)
            result.append(cont)
        return result

    def list_images(self):
        """
        List all available docker images.

        Image objects returned from this methods will contain a limited
        amount of metadata in property `short_metadata`. These are just a subset
        of `.inspect()`, but don't require an API call against dockerd.

        :return: collection of instances of :class:`conu.DockerImage`
        """
        response = []
        for im in self.d.images():
            try:
                i_name, tag = parse_reference(im["RepoTags"][0])
            except (IndexError, TypeError):
                i_name, tag = None, None
            d_im = DockerImage(i_name, tag=tag, identifier=im["Id"],
                               pull_policy=DockerImagePullPolicy.NEVER)
            inspect_to_metadata(d_im.metadata, im)

            response.append(d_im)
        return response

    def login(self, username, password=None, email=None, registry=None, reauth=False,
              dockercfg_path=None):
        """
        :param username: The registry username
        :param password: The plaintext password
        :param email: The email for the registry account
        :param registry: URL to the registry, example:
               - https://index.docker.io/v1/
        :param reauth: Whether or not to refresh existing authentication on the Docker server.
        :param dockercfg_path: Use a custom path for the Docker config file
        :return: None
        """
        self.d.login(username, password, email, registry, reauth, dockercfg_path)
        logger.info("Login to %s succeed", registry)

    def cleanup_volumes(self):
        # TODO implement cleaning of docker volumes
        pass

    def cleanup_images(self):
        # TODO implement cleaning of docker images
        pass

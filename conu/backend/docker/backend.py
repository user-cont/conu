"""
This is backend for docker engine
"""
import logging

from conu.apidefs.backend import Backend
from conu.backend.docker.container import DockerContainer
from conu.backend.docker.image import DockerImage
from conu.backend.docker.client import get_client
from conu.backend.docker.constants import CONU_ARTIFACT_TAG


logger = logging.getLogger(__name__)


# let this class inherit docstring from its parent
class DockerBackend(Backend):
    """
    For more info on using the Backend classes, see documentation of
    the parent :class:`conu.apidefs.backend.Backend` class.
    """
    ContainerClass = DockerContainer
    ImageClass = DockerImage

    @staticmethod
    def cleanup_containers():
        client = get_client()
        conu_containers = client.containers(filters={'label': CONU_ARTIFACT_TAG}, all=True)
        for c in conu_containers:
            id = c['Id']
            logger.debug("Removing container %s created by conu", id)
            client.stop(id)
            client.remove_container(id)

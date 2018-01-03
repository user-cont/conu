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


# TODO: use docker-py
# TODO: write some tests for this backend class
class DockerBackend(Backend):
    """
    This class groups classes related to a specific backend.
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

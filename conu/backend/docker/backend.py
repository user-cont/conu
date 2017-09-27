"""
This is backend for docker engine
"""

from conu.apidefs.backend import Backend
from conu.backend.docker.container import DockerContainer
from conu.backend.docker.image import DockerImage


# TODO: use docker-py
# TODO: write some tests for this backend class
class DockerBackend(Backend):
    """
    This class groups classes related to a specific backend.
    """

    ContainerClass = DockerContainer
    ImageClass = DockerImage

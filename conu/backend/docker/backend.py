"""
This is backend for docker engine
"""

from conu.apidefs.backend import Backend
from .container import Container
from .image import Image


# TODO: use docker-py
class DockerBackend(Backend):
    """
    This class groups classes related to a specific backend.
    """

    ContainerClass = Container
    ImageClass = Image

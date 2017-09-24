"""
Definition for a backend class
"""

from .container import Container
from .image import Image

class Backend(object):
    """
    This class groups classes related to a specific backend.
    """

    ContainerClass = Container
    ImageClass = Image

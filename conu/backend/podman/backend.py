"""
This is backend for podman engine
"""
import logging

from conu.apidefs.backend import Backend
from conu.backend.podman.container import PodmanContainer
from conu.backend.podman.image import PodmanImage

logger = logging.getLogger(__name__)


class PodmanBackend(Backend):
    """
    For more info on using the Backend classes, see documentation of
    the parent :class:`conu.apidefs.backend.Backend` class.
    """
    name = "podman"
    ContainerClass = PodmanContainer
    ImageClass = PodmanImage

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
        super(PodmanBackend, self).__init__(
            logging_level=logging_level, logging_kwargs=logging_kwargs, cleanup=cleanup)
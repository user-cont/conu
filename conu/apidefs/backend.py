"""
Definition for a backend class and logging initialization
"""
from __future__ import print_function, unicode_literals

import logging
import shutil

from conu.apidefs.container import Container
from conu.apidefs.image import Image
from conu import version
from conu.utils import mkdtemp


_backend_tmpdir = None


def get_backend_tmpdir():
    """
    provide tmpdir which is scoped for the whole backend

    :return: str, path to the temporary directory
    """
    global _backend_tmpdir
    if _backend_tmpdir is None:
        _backend_tmpdir = mkdtemp()
    return _backend_tmpdir


def set_logging(
        logger_name="conu",
        level=logging.INFO,
        handler_class=logging.StreamHandler,
        handler_kwargs=None,
        format='%(asctime)s.%(msecs).03d %(filename)-17s %(levelname)-6s %(message)s',
        date_format='%H:%M:%S'):
    """
    Set personal logger for this library.

    :param logger_name: str, name of the logger
    :param level: int, see logging.{DEBUG,INFO,ERROR,...}: level of logger and handler
    :param handler_class: logging.Handler instance, default is StreamHandler (/dev/stderr)
    :param handler_kwargs: dict, keyword arguments to handler's constructor
    :param format: str, formatting style
    :param date_format: str, date style in the logs
    :return: logger instance
    """
    logger = logging.getLogger(logger_name)
    # do we want to propagate to root logger?
    # logger.propagate = False
    logger.setLevel(level)

    handler_kwargs = handler_kwargs or {}
    handler = handler_class(**handler_kwargs)
    handler.setLevel(level)

    formatter = logging.Formatter(format, date_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class Backend(object):
    """
    This class groups classes related to a specific backend.
    """

    ContainerClass = Container
    ImageClass = Image

    def __init__(self, logging_level=logging.INFO, logging_kwargs=None):
        """
        This method serves as a configuration interface for conu.

        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        """
        self.tmpdir = get_backend_tmpdir()

        self.logging_level = logging_level
        logging_kwargs = logging_kwargs or {}
        self.logger = set_logging(level=self.logging_level, **logging_kwargs)
        self.logger.info("conu has initiated, welcome to the party!")
        self.logger.debug("conu version: %s", version.__version__)

    # TODO: provide backend as context manager, this just doesn't work
    #     File "conu/apidefs/backend.py", line 93, in __del__
    #   TypeError: 'NoneType' object is not callable
    #     "'NoneType' object has no attribute 'rmtree'"
    def __del__(self):
        def onerror(fnc, path, excinfo):
            # we might not have rights to do this, the files could be owned by root
            self.logger.info("we were not able to remove temporary file %s: %s", path, excinfo[1])
        shutil.rmtree(self.tmpdir, onerror=onerror)
        self.tmpdir = None
        global _backend_tmpdir
        _backend_tmpdir = None

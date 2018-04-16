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
Definition for a backend class and logging initialization
"""
from __future__ import print_function, unicode_literals

import logging
import shutil
import enum

from conu.apidefs.container import Container
from conu.apidefs.image import Image
from conu import version
from conu.utils import mkdtemp
from conu.exceptions import ConuException


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
    This class groups classes and functionality related to a specific backend.

    We strongly advise you to use backend as a context manager:

    ::

        with SomeBackend() as backend:
            image = backend.ImageClass(...)

    When entering the context manager, the backend will create a new temporary directory.
    You can use it if you want, the path is stored in attribute `tmpdir` of the backend instance.
    Some backend implementations use this temporary directory to store some short-lived
    runtime files (e.g. container-id file in case of docker). Once the context manager goes
    out of scope, this temporary directory is removed. If you don't use the backend class as a
    context manager, the temporary directory isn't removed and therefore lingers.
    """

    name = "<abstract_backend>"
    ContainerClass = Container
    ImageClass = Image

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
        self.tmpdir = None

        self.logging_level = logging_level
        logging_kwargs = logging_kwargs or {}
        self.logger = set_logging(level=self.logging_level, **logging_kwargs)
        self.logger.info("conu has initiated, welcome to the party!")
        self.logger.debug("conu version: %s", version.__version__)

        self.cleanup = cleanup or [CleanupPolicy.NOTHING]

    def list_containers(self):
        """
        list all available containers for this backend

        :return: collection of instances of :class:`conu.apidefs.container.Container`
        """
        raise NotImplementedError("list_images method is not implemented")

    def list_images(self):
        """
        list all available images for this backend

        :return: collection of instances of :class:`conu.apidefs.image.Image`
        """
        raise NotImplementedError("list_images method is not implemented")

    def _clean_tmp_dirs(self):
        """
        Remove temporary dir associated with this backend instance.

        :return: None
        """

        def onerror(fnc, path, excinfo):
            # we might not have rights to do this, the files could be owned by root
            self.logger.info("we were not able to remove temporary file %s: %s", path, excinfo[1])

        shutil.rmtree(self.tmpdir, onerror=onerror)
        self.tmpdir = None
        global _backend_tmpdir
        _backend_tmpdir = None

    def cleanup_containers(self):
        """
        Remove containers associated with this backend instance

        :return: None
        """
        raise NotImplementedError("cleanup_containers method is not implemented")

    def cleanup_volumes(self):
        """
        Remove volumes associated with this backend instance

        :return: None
        """
        raise NotImplementedError("cleanup_volumes method is not implemented")

    def cleanup_images(self):
        """
        Remove images associated with this backend instance

        :return: None
        """
        raise NotImplementedError("cleanup_images method is not implemented")

    def _clean(self):

        if CleanupPolicy.NOTHING in self.cleanup and len(self.cleanup) != 1:
            raise ConuException("Cleanup policy NOTHING cannot be combined with other values")
        elif CleanupPolicy.EVERYTHING in self.cleanup:
                self.cleanup_containers()
                self.cleanup_volumes()
                self.cleanup_images()
                self._clean_tmp_dirs()
        else:
            if CleanupPolicy.CONTAINERS in self.cleanup:
                self.cleanup_containers()
            if CleanupPolicy.VOLUMES in self.cleanup:
                self.cleanup_volumes()
            if CleanupPolicy.IMAGES in self.cleanup:
                self.cleanup_images()
            if CleanupPolicy.TMP_DIRS in self.cleanup:
                self._clean_tmp_dirs()

    def __enter__(self):
        self.tmpdir = get_backend_tmpdir()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._clean()


class CleanupPolicy(enum.Enum):
    """
    This Enum defines the policy for cleanup.

    * NOTHING - clean nothing when container exits
    * EVERYTHING - clean everything when container exits (containers, volumes, images, temporary directories)
    * CONTAINERS - remove containers
    * VOLUMES - remove all volumes
    * IMAGES - remove the image
    * TMP_DIRS - remove temporary directories
    """
    NOTHING = 0
    EVERYTHING = 1
    CONTAINERS = 2
    VOLUMES = 3
    IMAGES = 4
    TMP_DIRS = 5

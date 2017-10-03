# -*- coding: utf-8 -*-
"""
Utilities related to manipulate docker images.
"""
from __future__ import print_function, unicode_literals

import logging
import subprocess

from conu.apidefs.exceptions import ConuException
from conu.apidefs.filesystem import Filesystem
from conu.apidefs.image import Image
from conu.backend.docker.client import get_client


logger = logging.getLogger(__name__)


class DockerImageFS(Filesystem):
    def __init__(self, image, mount_point=None):
        """
        :param image: instance of DockerImage
        :param mount_point: str, directory where the filesystem will be mounted
        """
        super(DockerImageFS, self).__init__(image, mount_point=mount_point)
        self.image = image

    def __enter__(self):
        # FIXME: I'm not sure about this, is doing docker save/export better?
        subprocess.check_call(["atomic", "mount", self.image.get_full_name(), self.mount_point])
        return super(DockerImageFS, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.check_call(["atomic", "umount", self.mount_point])
        return super(DockerImageFS, self).__exit__(exc_type, exc_val, exc_tb)


class DockerImage(Image):
    """
    Utility functions for docker images.
    """
    def __init__(self, repository, tag="latest"):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        """
        super(DockerImage, self).__init__(repository, tag=tag)
        self.tag = self.tag
        self.d = get_client()

    def __repr__(self):
        return "DockerImage(repository=%s, tag=%s)" % (self.name, self.tag)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Provide full, complete image name

        :return: str
        """
        return "%s:%s" % (self.name, self.tag)

    def get_id(self):
        """
        get unique identifier of this image

        :return: str
        """
        if self._id is None:
            self._id = self.get_metadata(refresh=False)["Id"]
        return self._id

    def pull(self):
        """
        pull this image

        :return: None
        """
        for o in self.d.pull(repository=self.name, tag=self.tag, stream=True):
            logger.debug(o)

    def tag_image(self, repository=None, tag=None):
        """
        Apply additional tags to the image or even add a new name

        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: instance of DockerImage
        """
        if not (repository or tag):
            raise ValueError("You need to specify either repository or tag.")
        r = repository or self.name
        t = "latest" if not tag else tag
        self.d.tag(image=self.get_full_name(), repository=r, tag=t)
        return DockerImage(r, tag=t)

    def inspect(self, refresh=True):
        """
        return cached metadata by default (a convenience method)

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        return self.get_metadata(refresh=refresh)

    def get_metadata(self, refresh=True):
        """
        return cached metadata by default

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        if refresh or not self._metadata:
            ident = self._id or self.get_full_name()
            if not ident:
                raise ConuException("This image does not have a valid identifier.")
            self._metadata = self.d.inspect_image(ident)
        return self._metadata

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        self.d.remove_image(self.get_full_name() if via_name else self.get_id(), force=force)

    def mount(self, mount_point=None):
        """
        mount image filesystem

        :param mount_point: str, directory where the filesystem will be mounted
        :return: instance of DockerImageFS
        """
        return DockerImageFS(self, mount_point=mount_point)

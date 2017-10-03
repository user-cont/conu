# -*- coding: utf-8 -*-

"""
Utilities related to manipulate docker images.
"""

import json

from conu.apidefs.image import Image
from conu.utils.core import run_cmd


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
        run_cmd("docker image pull %s" % self.get_full_name())

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
        image_name = "%s:%s" % (r, t)
        run_cmd("docker image tag %s %s" % (self.get_full_name(), image_name))
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
            self._metadata = json.loads(run_cmd("docker image inspect %s" % self.get_full_name()))[0]
        return self._metadata

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        run_cmd("docker image remove %s%s" % (
            "-f " if force else "",
            self.get_full_name() if via_name else self.get_id())
        )

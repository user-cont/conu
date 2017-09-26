# -*- coding: utf-8 -*-

import json

from conu.apidefs.image import Image
from conu.utils.core import run_cmd


class DockerImage(Image):
    """
    A class which represents a docker container image. It contains utility methods to manipulate it.
    """
    def __init__(self, repository, tag=None):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        """
        self.tag = tag or "latest"
        self.name = repository
        self.inspect_data = None
        self.additional_names = []

    def full_name(self):
        return "%s:%s" % (self.name, self.tag)

    def pull(self):
        run_cmd("docker image pull %s" % self.full_name())

    def tag_image(self, repository=None, tag=None):
        """
        Apply additional tags to the image or even add a new name

        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: str, the new name
        """
        if not (repository or tag):
            raise ValueError("You need to specify either repository or tag.")
        t = repository or self.name
        t = "%s:%s" % (t, "latest" if not tag else tag)
        run_cmd("docker image tag %s %s" % (self.full_name(), t))
        self.additional_names.append(t)
        return t

    def __repr__(self):
        return "Image(repository=%s, tag=%s)" % (self.name, self.tag)

    def __str__(self):
        return self.full_name()

    def inspect(self, force=False):
        if force or not self.inspect_data:
            self.inspect_data = json.loads(run_cmd("docker image inspect %s" % self.full_name()))[0]
        return self.inspect_data

    @classmethod
    def rmi(cls, image, force=False):
        """
        remove selected image

        :param image: str, image name, example: "fedora:latest"
        :return: None
        """
        run_cmd("docker image remove %s%s" % ("-f " if force else "",  image))

    def clean(self, force=False):
        images_to_remove = self.additional_names + [self.full_name()]
        for i in images_to_remove:
            DockerImage.rmi(i, force=force)
        self.additional_names = []

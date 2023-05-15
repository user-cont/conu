# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

"""
Utilities related to manipulate buildah images.
"""
from __future__ import print_function, unicode_literals

import enum
import json
import logging
import os
import subprocess

from conu.apidefs.backend import get_backend_tmpdir
from conu.apidefs.image import Image
from conu.apidefs.metadata import ImageMetadata
from conu.backend.buildah.container import BuildahContainer, BuildahRunBuilder
from conu.backend.buildah.utils import buildah_common_inspect_to_metadata
from conu.exceptions import ConuException
from conu.utils import run_cmd, random_tmp_filename, graceful_get
from conu.utils.filesystem import Volume
from conu.utils.probes import Probe

logger = logging.getLogger(__name__)


class BuildahImagePullPolicy(enum.Enum):
    """
    This Enum defines the policy for pulling the buildah images. The pull operation happens when
    creating an instance of a buildah image. Supported values:

    * NEVER - do not pull the image
    * IF_NOT_PRESENT - pull it only if the image is not present
    * ALWAYS - always initiate the pull process - the image is being pulled even if it's present
      locally. It means that it may be overwritten by a remote counterpart or there may
      be a exception being raised if no such image is present in the registry.
    """
    NEVER = 0
    IF_NOT_PRESENT = 1
    ALWAYS = 2


def buildah_image_inspect_to_metadata(inspect_data):
    """
    process data from `buildah inspect -t image` and return ImageMetadata

    :param inspect_data: dict, metadata from `buildah inspect -t image`
    :return: instance of ImageMetadata
    """
    im = ImageMetadata()
    im.name = graceful_get(inspect_data, "FromImage")
    im.identifier = graceful_get(inspect_data, "FromImageID")
    buildah_common_inspect_to_metadata(im, inspect_data)
    return im


class BuildahImage(Image):
    """
    Utility functions for buildah images.
    """

    def __init__(self, repository, tag="latest", identifier=None,
                 pull_policy=BuildahImagePullPolicy.IF_NOT_PRESENT):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        :param identifier: str, unique identifier for this image
        :param pull_policy: enum, strategy to apply for pulling the image
        """
        super(BuildahImage, self).__init__(repository, tag=tag)
        if not isinstance(tag, (str, None.__class__)):
            raise ConuException("'tag' is not a string type")
        if not isinstance(pull_policy, BuildahImagePullPolicy):
            raise ConuException("'pull_policy' is not an instance of BuildahImagePullPolicy")
        if identifier:
            self._id = identifier
        self.pull_policy = pull_policy

        self._inspect_data = None
        self._metadata = None

        if self.pull_policy == BuildahImagePullPolicy.ALWAYS:
            logger.debug("pull policy set to 'always', pulling the image")
            self.pull()
        elif self.pull_policy == BuildahImagePullPolicy.IF_NOT_PRESENT and not self.is_present():
            logger.debug("pull policy set to 'if_not_present' and image is not present, "
                         "pulling the image")
            self.pull()
        elif self.pull_policy == BuildahImagePullPolicy.NEVER:
            logger.debug("pull policy set to 'never'")

    def __repr__(self):
        return "BuildahImage(repository=%s, tag=%s)" % (self.name, self.tag)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Provide full, complete image name

        :return: str
        """
        if self.name:
            return "%s:%s" % (self.name, self.tag)
        else:
            return self.name

    def get_id(self):
        """
        get unique identifier of this image

        :return: str
        """
        if self._id is None:
            self._id = graceful_get(self.inspect(refresh=False), "FromImageID")
        return self._id

    def is_present(self):
        """
        Is this buildah image present locally on the system?

        :return: bool, True if it is, False if it's not
        """
        try:
            return bool(self.inspect())
        except subprocess.CalledProcessError:
            return False

    def pull(self):
        """
        Pull this image from registry. Raises an exception if the image is not found in
        the registry.

        :return: None
        """
        full_name = self.get_full_name()
        if full_name == "scratch:latest":
            logger.warning("scratch image can't be pulled")
            return
        run_cmd(["buildah", "pull", self.get_full_name()])

    def tag_image(self, repository=None, tag=None):
        """
        Apply additional tags to the image or a new name
        >> buildah tag image[:tag] target-name[:tag]

        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: instance of BuildahImage
        """
        if not (repository or tag):
            raise ValueError("You need to specify either repository or tag.")
        r = repository or self.name
        t = tag or "latest"
        identifier = self._id or self.get_id()
        run_cmd(["buildah", "tag", identifier, "%s:%s" % (r, t)])
        return BuildahImage(r, tag=t)

    def inspect(self, refresh=True):
        """
        provide metadata about the image; flip refresh=True if cached metadata are enough

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        if refresh or not self._inspect_data:
            identifier = self._id or self.get_full_name()
            if not identifier:
                raise ConuException("This image does not have a valid identifier.")
            self._inspect_data = self._inspect(identifier)
        return self._inspect_data

    @staticmethod
    def _inspect(identifier):
        cmdline = ['buildah', 'inspect', '--type', 'image', identifier]
        output = run_cmd(cmdline, return_output=True, log_output=False)
        return json.loads(output)

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        identifier = self.get_full_name() if via_name else (self._id or self.get_id())
        cmdline = ["buildah", "rmi"]
        if force:
            # buildah doesn't like the trailing ""
            cmdline += ["--force"]
        run_cmd(cmdline + [identifier])

    @staticmethod
    def _file_not_empty(tmpfile):
        """
        Returns True if file exists and it is not empty
        to check if it is time to read container ID from cidfile
        :param tmpfile: str, path to file
        :return: bool, True if container id is written to the file
        """
        if os.path.exists(tmpfile):
            return os.stat(tmpfile).st_size != 0
        else:
            return False

    def run_via_binary(self, run_command_instance=None, command=None, volumes=None,
                       additional_opts=None, **kwargs):
        """
        create a buildah container using this image

        :param run_command_instance: not used
        :param command: not used, please use exec
        :param volumes: tuple or list of tuples in the form:
            * `("/path/to/directory", )`
            * `("/host/path", "/container/path")`
            * `("/host/path", "/container/path", "mode")`
            * `(conu.Directory('/host/path'), "/container/path")` (source can be also
                Directory instance)

        :param additional_opts: list of str, additional options for `buildah from`
        :return: instance of BuildahContainer
        """
        logger.info("create buildah container")
        if not run_command_instance:
            run_command_instance = BuildahRunBuilder(
                command=command,
                additional_opts=additional_opts
            )
        run_command_instance.image_name = self.get_full_name()
        tmpfile = os.path.join(get_backend_tmpdir(), random_tmp_filename())
        run_command_instance.options += ["--cidfile=%s" % tmpfile]

        # TODO: add support for the skopeo transport names

        cmd = run_command_instance.build()

        # TODO: fix this using the run builder
        # if volumes:
        #     cmd += self.get_volume_options(volumes=volumes)

        run_cmd(cmd)

        Probe(timeout=10, count=10, pause=0.1, fnc=lambda: self._file_not_empty(tmpfile)).run()
        with open(tmpfile, 'r') as fd:
            container_id = fd.read()

        return BuildahContainer(self, container_id, image_class=self.__class__)

    @staticmethod
    def get_volume_options(volumes):
        """
        Generates volume options to run methods.

        :param volumes: tuple or list of tuples in form target x source,target x source,target,mode.
        :return: list of the form ["-v", "/source:/target", "-v", "/other/source:/destination:z", ...]
        """
        if not isinstance(volumes, list):
            volumes = [volumes]
        volumes = [Volume.create_from_tuple(v) for v in volumes]
        result = []
        for v in volumes:
            result += ["-v", str(v)]
        return result

    def get_layer_ids(self, rev=True):
        """
        Get IDs of image layers

        :param rev: get layers reversed
        :return: list of strings
        """
        cmdline = ["buildah", "history", "--format", "{{.ID}}", self._id or self.get_id()]
        layers = [layer for layer in run_cmd(cmdline, return_output=True)]
        if not rev:
            layers = layers.reverse()
        return layers

    def layers(self, rev=True):
        """
        Get list of BuildahImage for every layer in image

        :param rev: get layers rev
        :return: list of :class:`conu.BuildahImage`
        """
        image_layers = [
            BuildahImage(None, identifier=x, pull_policy=BuildahImagePullPolicy.NEVER)
            for x in self.get_layer_ids()
        ]
        if not rev:
            image_layers.reverse()
        return image_layers

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self.get_metadata()
        return self._metadata

    def get_metadata(self):
        """
        Provide metadata about this image.

        :return: ImageMetadata, Image metadata instance
        """
        if self._metadata is None:
            self._metadata = buildah_image_inspect_to_metadata(self.inspect(refresh=True))
        return self._metadata

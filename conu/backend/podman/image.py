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
Utilities related to manipulate podman images.
"""
from __future__ import print_function, unicode_literals

import logging
import os
import subprocess
import enum

import six

import podman

from conu.apidefs.metadata import ImageMetadata
from conu.apidefs.backend import get_backend_tmpdir
from conu.apidefs.image import Image

from conu.backend.podman.client import get_client
from conu.backend.podman.container import PodmanContainer, PodmanRunBuilder

from conu.backend.docker.image import DockerImageViaArchiveFS

from conu.exceptions import ConuException
from conu.utils import run_cmd, random_tmp_filename, \
    graceful_get, export_docker_container_to_directory
from conu.utils.filesystem import Volume
from conu.utils.probes import Probe


logger = logging.getLogger(__name__)


class PodmanImageViaArchiveFS(DockerImageViaArchiveFS):
    def __init__(self, image, mount_point=None):
        """
        Provide image as an archive

        :param image: instance of PodmanImage
        :param mount_point: str, directory where the filesystem will be made available
        """
        super(PodmanImageViaArchiveFS, self).__init__(image, mount_point=mount_point)
        self.image = image

    def __enter__(self):
        client = get_client()
        c = client.create_container(self.image.get_id())
        container = PodmanContainer(self.image, c["Id"])
        try:
            export_docker_container_to_directory(client, container, self.mount_point)
        finally:
            container.delete(force=True)
        return super(PodmanImageViaArchiveFS, self).__enter__()


class PodmanImagePullPolicy(enum.Enum):
    """
    This Enum defines the policy for pulling the podman images. The pull operation happens when
    creating an instance of a podman image. Supported values:

    * NEVER - do not pull the image
    * IF_NOT_PRESENT - pull it only if the image is not present
    * ALWAYS - always initiate the pull process - the image is being pulled even if it's present
      locally. It means that it may be overwritten by a remote counterpart or there may
      be a exception being raised if no such image is present in the registry.
    """
    NEVER = 0
    IF_NOT_PRESENT = 1
    ALWAYS = 2


class PodmanImage(Image):
    """
    Utility functions for podman images.
    """

    def __init__(self, repository, tag="latest", identifier=None,
                 pull_policy=PodmanImagePullPolicy.IF_NOT_PRESENT):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        :param identifier: str, unique identifier for this image
        :param pull_policy: enum, strategy to apply for pulling the image
        """
        super(PodmanImage, self).__init__(repository, tag=tag)
        if not isinstance(tag, (six.string_types, None.__class__)):
            raise ConuException("'tag' is not a string type")
        if not isinstance(pull_policy, PodmanImagePullPolicy):
            raise ConuException("'pull_policy' is not an instance of PodmanImagePullPolicy")
        if identifier:
            self._id = identifier
        self.d = get_client()
        self.pull_policy = pull_policy

        self._inspect_data = None
        self.metadata = ImageMetadata()

        if self.pull_policy == PodmanImagePullPolicy.ALWAYS:
            logger.debug("pull policy set to 'always', pulling the image")
            self.pull()
        elif self.pull_policy == PodmanImagePullPolicy.IF_NOT_PRESENT and not self.is_present():
            logger.debug("pull policy set to 'if_not_present' and image is not present, "
                         "pulling the image")
            self.pull()
        elif self.pull_policy == PodmanImagePullPolicy.NEVER:
            logger.debug("pull policy set to 'never'")

    def __repr__(self):
        return "PodmanImage(repository=%s, tag=%s)" % (self.name, self.tag)

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
            self._id = self.inspect(refresh=False)["id"]
        return self._id

    def is_present(self):
        """
        Is this podman image present locally on the system?

        :return: bool, True if it is, False if it's not
        """
        # TODO: move this method to generic API
        try:
            return bool(self.inspect())
        except podman.libs.errors.ImageNotFound:
            return False

    def pull(self):
        """
        Pull this image from registry. Raises an exception if the image is not found in
        the registry.

        :return: None
        """
        for json_e in self.d.images.pull(self.get_full_name()):
            logger.debug(json_e)
            status = graceful_get(json_e, "status")
            if status:
                logger.info(status)
            else:
                error = graceful_get(json_e, "error")
                logger.error(status)
                raise ConuException("There was an error while pulling the image %s: %s",
                                    self.get_full_name(), error)

    def tag_image(self, repository=None, tag=None):
        """
        Apply additional tags to the image BUT NOT A NEW NAME

        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: instance of PodmanImage
        """
        if not (repository or tag):
            raise ValueError("You need to specify either repository or tag.")
        r = repository or self.name
        t = "latest" if not tag else tag
        i = self._id or self.get_id()
        self.d.images.get(i).tag(tag="%s:%s" % (r, t))
        return PodmanImage(r, tag=t)

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
            self._inspect_data = self.d.images.get(identifier).inspect()
            # Convert to dict
            self._inspect_data = dict(self._inspect_data._asdict())
        return self._inspect_data

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        # FIXME: There is no 'via name' remove method in podman python API
        if via_name:
            cmdline = ["podman", "rmi", self.get_full_name()]
            if force: cmdline.insert(2, "--force")
            run_cmd(cmdline)
        else:
            self.d.images.get(self.get_id()).remove(force=force)

    def _run_container(self, run_command_instance, callback):
        """ this is internal method """
        tmpfile = os.path.join(get_backend_tmpdir(), random_tmp_filename())
        # the cid file must not exist
        run_command_instance.options += ["--cidfile=%s" % tmpfile]
        logger.debug("podman command: %s" % run_command_instance)
        response = callback()
        # and we need to wait now; inotify would be better but is way more complicated and
        # adds dependency
        Probe(timeout=10, count=10, pause=0.1, fnc=lambda: os.path.exists(tmpfile)).run()
        with open(tmpfile, 'r') as fd:
            container_id = fd.read()
        return container_id, response

    def run_via_binary(self, run_command_instance=None, command=None, volumes=None,
                       additional_opts=None, **kwargs):
        """
        create a container using this image and run it in background;
        this method is useful to test real user scenarios when users invoke containers using
        binary

        :param run_command_instance: instance of PodmanRunBuilder
        :param command: list of str, command to run in the container, examples:
            - ["ls", "/"]
            - ["bash", "-c", "ls / | grep bin"]
        :param volumes: tuple or list of tuples in the form:

            * `("/path/to/directory", )`
            * `("/host/path", "/container/path")`
            * `("/host/path", "/container/path", "mode")`
            * `(conu.Directory('/host/path'), "/container/path")` (source can be also
                Directory instance)

        :param additional_opts: list of str, additional options for `podman run`
        :return: instance of PodmanContainer
        """

        logger.info("run container via binary in background")

        if (command is not None or additional_opts is not None) \
                and run_command_instance is not None:
            raise ConuException(
                "run_command_instance and command parameters cannot be passed "
                "into method at same time")

        if run_command_instance is None:
            command = command or []
            additional_opts = additional_opts or []

            if (isinstance(command, list) or isinstance(command, tuple) and
                isinstance(additional_opts, list) or isinstance(additional_opts, tuple)):
                run_command_instance = PodmanRunBuilder(
                    command=command, additional_opts=additional_opts)
            else:
                raise ConuException("command and additional_opts needs to be list of str or None")
        else:
            run_command_instance = run_command_instance or PodmanRunBuilder()
            if not isinstance(run_command_instance, PodmanRunBuilder):
                raise ConuException(
                    "run_command_instance needs to be an instance of PodmanRunBuilder")

        run_command_instance.image_name = self.get_id()

        # FIXME: podman exits with error 139 if no --privileged flag
        run_command_instance.options += ["-d", "--privileged"]

        if volumes:
            run_command_instance.options += self.get_volume_options(volumes=volumes)

        def callback():
            try:
                # FIXME: catch std{out,err}, print stdout to logger.debug, stderr to logger.error
                run_cmd(run_command_instance.build())
            except subprocess.CalledProcessError as ex:
                raise ConuException("Container exited with an error: %s" % ex.returncode)

        container_id, _ = self._run_container(run_command_instance, callback)

        container_name = self.d.containers.get(container_id).inspect().name
        return PodmanContainer(self, container_id, name=container_name)

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

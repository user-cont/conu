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
import json
import six

from conu.apidefs.metadata import ImageMetadata
from conu.apidefs.backend import get_backend_tmpdir
from conu.apidefs.image import Image

from conu.backend.podman.container import PodmanContainer, PodmanRunBuilder
from conu.backend.podman.utils import inspect_to_metadata

from conu.exceptions import ConuException

from conu.utils import run_cmd, random_tmp_filename, graceful_get
from conu.utils.filesystem import Volume
from conu.utils.probes import Probe


logger = logging.getLogger(__name__)


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
        self.pull_policy = pull_policy

        self._inspect_data = None
        self._metadata = None

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
            self._id = graceful_get(self.inspect(refresh=False), "Id")
        return self._id

    def is_present(self):
        """
        Is this podman image present locally on the system?

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
        run_cmd(["podman", "pull", self.get_full_name()])

    def tag_image(self, repository=None, tag=None):
        """
        Apply additional tags to the image or a new name
        >> podman tag image[:tag] target-name[:tag]

        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: instance of PodmanImage
        """
        if not (repository or tag):
            raise ValueError("You need to specify either repository or tag.")
        r = repository or self.name
        t = tag or "latest"
        identifier = self._id or self.get_id()
        run_cmd(["podman", "tag", identifier, "%s:%s" % (r, t)])
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
            self._inspect_data = self._inspect(identifier)
        return self._inspect_data

    @staticmethod
    def _inspect(identifier):
        cmdline = ['podman', 'inspect', identifier]
        output = run_cmd(cmdline, return_output=True, log_output=False)
        return json.loads(output)[0]

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        identifier = self.get_full_name() if via_name else (self._id or self.get_id())
        cmdline = ["podman", "rmi", identifier, "--force" if force else ""]
        run_cmd(cmdline)

    def _run_container(self, run_command_instance, callback):
        """ this is internal method """
        tmpfile = os.path.join(get_backend_tmpdir(), random_tmp_filename())
        # the cid file must not exist
        run_command_instance.options += ["--cidfile=%s" % tmpfile]
        logger.debug("podman command: %s" % run_command_instance)
        response = callback()
        # and we need to wait now; inotify would be better but is way more complicated and
        # adds dependency
        Probe(timeout=10, count=10, pause=0.1, fnc=lambda: self._file_not_empty(tmpfile)).run()
        with open(tmpfile, 'r') as fd:
            container_id = fd.read()
        return container_id, response

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
        run_command_instance.options += ["-d"]

        if volumes:
            run_command_instance.options += self.get_volume_options(volumes=volumes)

        def callback():
            try:
                # FIXME: catch std{out,err}, print stdout to logger.debug, stderr to logger.error
                run_cmd(run_command_instance.build())
            except subprocess.CalledProcessError as ex:
                raise ConuException("Container exited with an error: %s" % ex.returncode)

        container_id, _ = self._run_container(run_command_instance, callback)
        container_name = graceful_get(self._inspect(container_id), "Name")

        return PodmanContainer(self, container_id, name=container_name)

    def run_via_binary_in_foreground(
            self, run_command_instance=None, command=None, volumes=None,
            additional_opts=None, popen_params=None, container_name=None):
        """
        Create a container using this image and run it in foreground;
        this method is useful to test real user scenarios when users invoke containers using
        binary and pass input into the container via STDIN. You are also responsible for:

         * redirecting STDIN when intending to use container.write_to_stdin afterwards by setting
              popen_params={"stdin": subprocess.PIPE} during run_via_binary_in_foreground

         * checking whether the container exited successfully via:
              container.popen_instance.returncode

        Please consult the documentation for subprocess python module for best practices on
        how you should work with instance of Popen

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

        :param additional_opts: list of str, additional options for `docker run`
        :param popen_params: dict, keyword arguments passed to Popen constructor
        :param container_name: str, pretty container identifier
        :return: instance of PodmanContainer
        """
        logger.info("run container via binary in foreground")

        if (command is not None or additional_opts is not None) \
                and run_command_instance is not None:
            raise ConuException(
                "run_command_instance and command parameters cannot be "
                "passed into method at same time")

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
                raise ConuException("run_command_instance needs to be an "
                                    "instance of PodmanRunBuilder")

        popen_params = popen_params or {}

        run_command_instance.image_name = self.get_id()
        if container_name:
            run_command_instance.options += ["--name", container_name]

        if volumes:
            run_command_instance.options += self.get_volume_options(volumes=volumes)

        def callback():
            return subprocess.Popen(run_command_instance.build(), **popen_params)

        container_id, popen_instance = self._run_container(run_command_instance, callback)

        actual_name = graceful_get(self._inspect(container_id), "Name")

        if container_name and container_name != actual_name:
            raise ConuException(
                "Unexpected container name value. Expected = "
                + str(container_name) + " Actual = " + str(actual_name))
        if not container_name:
            container_name = actual_name
        return PodmanContainer(
            self, container_id, popen_instance=popen_instance, name=container_name)

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
        cmdline = ["podman", "history", "--format", "{{.ID}}", self._id or self.get_id()]
        layers = [layer for layer in run_cmd(cmdline, return_output=True)]
        if not rev:
            layers = layers.reverse()
        return layers

    def layers(self, rev=True):
        """
        Get list of PodmanImage for every layer in image

        :param rev: get layers rev
        :return: list of :class:`conu.PodmanImage`
        """
        image_layers = [
            PodmanImage(None, identifier=x, pull_policy=PodmanImagePullPolicy.NEVER)
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
            self._metadata = ImageMetadata()
        inspect_to_metadata(self._metadata, self.inspect(refresh=True))
        return self._metadata

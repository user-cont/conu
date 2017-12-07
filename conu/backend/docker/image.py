# -*- coding: utf-8 -*-
"""
Utilities related to manipulate docker images.
"""
from __future__ import print_function, unicode_literals

import logging
import os
import shutil
import subprocess

from conu.apidefs.filesystem import Filesystem
from conu.apidefs.image import Image, S2Image
from conu.backend.docker.client import get_client
from conu.backend.docker.container import DockerContainer, DockerRunBuilder
from conu.exceptions import ConuException
from conu.utils import run_cmd

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
        run_cmd(["atomic", "mount", self.image.get_full_name(), self.mount_point])
        return super(DockerImageFS, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        run_cmd(["atomic", "umount", self.mount_point])
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

    def run_via_binary(self, run_command_instance=None, *args, **kwargs):
        """
        create a container using this image and run it in background;
        this method is useful to test real user scenarios when users invoke containers using
        binary

        :param image: instance of Image
        :param run_command_instance: instance of DockerRunBuilder
        :return: instance of DockerContainer
        """
        logger.info("run container via binary in background")
        run_command_instance = run_command_instance or DockerRunBuilder()
        if not isinstance(run_command_instance, DockerRunBuilder):
            raise ConuException("run_command_instance needs to be an instance of DockerRunBuilder")
        run_command_instance.image_name = self.get_id()
        run_command_instance.options += ["-d"]
        popen_instance = subprocess.Popen(run_command_instance.build(), stdout=subprocess.PIPE)
        stdout = popen_instance.communicate()[0].strip().decode("utf-8")
        if popen_instance.returncode > 0:
            raise ConuException("Container exited with an error: %s" % popen_instance.returncode)
        # no error, stdout is the container id
        return DockerContainer(self, stdout)

    def run_via_binary_in_foreground(
            self, run_command_instance=None, popen_params=None, container_name=None):
        """
        Create a container using this image and run it in foreground;
        this method is useful to test real user scenarios when users invoke containers using
        binary and pass input into the container via STDIN. Please bear in mind that conu doesn't
        know the ID of the container when created like this, so it's highly recommended to name
        your container. You are also responsible for checking whether the container exited
        successfully via:

            container.popen_instance.returncode

        Please consult the documentation for subprocess python module for best practices on
        how you should work with instance of Popen

        :param run_command_instance: instance of DockerRunBuilder
        :param popen_params: dict, keyword arguments passed to Popen constructor
        :param container_name: str, pretty container identifier
        :return: instance of DockerContainer
        """
        logger.info("run container via binary in foreground")
        run_command_instance = run_command_instance or DockerRunBuilder()
        if not isinstance(run_command_instance, DockerRunBuilder):
            raise ConuException("run_command_instance needs to be an instance of DockerRunBuilder")
        popen_params = popen_params or {}
        run_command_instance.image_name = self.get_id()
        if container_name:
            run_command_instance.options += ["--name", container_name]
        logger.debug("command = %s", str(run_command_instance))
        popen_instance = subprocess.Popen(run_command_instance.build(), **popen_params)
        container_id = None
        return DockerContainer(self, container_id, popen_instance=popen_instance, name=container_name)

class S2IDockerImage(DockerImage, S2Image):
    def __init__(self, repository, tag="latest"):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        """
        super(S2IDockerImage, self).__init__(repository, tag=tag)
        self._s2i_exists = None

    @property
    def s2i_exists(self):
        if self._s2i_exists is None:
            try:
                self._s2i_exists = bool(shutil.which("s2i"))  # py3 only
            except AttributeError:
                with open(os.devnull, "w") as fd:
                    try:
                        rc = subprocess.call(["s2i", "version"], stdout=fd, stderr=fd)
                    except OSError:
                        self._s2i_exists = False
                    else:
                        if rc != 0:
                            logger.error("`s2i version` exited with a non-zero return code, please"
                                         " check your s2i binary if it's okay")
                            # FIXME: I dunno, raise an error? Or leap of faith?
                        self._s2i_exists = True
        return self._s2i_exists

    def _s2i_command(self, args):
        """
        return s2i command to run

        :param args: list of str, arguments and options passed to s2i binary
        :return: list of str
        """
        if not self.s2i_exists:
            raise ConuException("s2i executable is not available, please install it "
                                "(https://github.com/openshift/source-to-image)")
        return ["s2i"] + args

    def extend(self, source, new_image_name, s2i_args=None):
        """
        extend this s2i-enabled image using provided source, raises ConuException if
        `s2i build` fails

        :param source: str, source used to extend the image, can be path or url
        :param new_image_name: str, name of the new, extended image
        :param s2i_args: list of str, additional options and arguments provided to `s2i build`
        :return: S2Image instance
        """
        s2i_args = s2i_args or []
        c = self._s2i_command(["build"] + s2i_args + [source, self.get_full_name()])
        if new_image_name:
            c.append(new_image_name)
        try:
            run_cmd(c)
        except subprocess.CalledProcessError as ex:
            raise ConuException("s2i build failed: %s" % ex)
        return S2IDockerImage(new_image_name)

    def usage(self):
        """
        Provide output of `s2i usage`

        :return: str
        """
        c = self._s2i_command(["usage", self.get_full_name()])
        with open(os.devnull, "w") as fd:
            process = subprocess.Popen(c, stdout=fd, stderr=subprocess.PIPE)
            _, output = process.communicate()
            retcode = process.poll()
        if retcode:
            raise ConuException("`s2i usage` failed: %s" % output)
        return output.decode("utf-8").strip()

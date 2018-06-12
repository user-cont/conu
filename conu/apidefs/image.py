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
Abstract definition for an Image
"""
from __future__ import print_function, unicode_literals


class Image(object):
    """
    A class which represents an arbitrary container image. It contains utility methods
    to manipulate it.
    """
    def __init__(self, image_reference, tag=None):
        """
        :param image_reference: str, the reference to this image (usually name)
        :param tag: str, tag of the image, when not specified, "latest" is implied
        """
        self.tag = tag
        self.name = image_reference
        self._metadata = None
        self._id = None

    def get_full_name(self):
        """
        provide full, complete image name

        :return: str
        """
        raise NotImplementedError("get_full_name method is not implemented")

    def get_id(self):
        """
        get unique identifier of this image

        :return: str
        """
        raise NotImplementedError("get_id method is not implemented")

    def pull(self):
        """
        pull this image

        :return: None
        """
        raise NotImplementedError("pull method is not implemented")

    @classmethod
    def load_from_file(cls, file_path):
        """
        load Image from provided file

        :param file_path: str, path to the file
        :return: Image instance
        """
        raise NotImplementedError("load_from_file method is not implemented")

    def inspect(self, refresh=False):
        """
        return cached metadata by default

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        raise NotImplementedError("inspect method is not implemented")

    def get_metadata(self):
        """
        return general metadata for image

        :return: ImageMetadata
        """
        raise NotImplementedError("get_metadata method is not implemented")

    def rmi(self, force=False, via_name=False):
        """
        remove selected image

        :param image: str, image name, example: "fedora:latest"
        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        raise NotImplementedError("rmi method is not implemented")

    def mount_image(self, mount_point=None):
        """
        mount an image to host system
        :param mount_point: str, mount_point on host system
        :return: mount_point
        """
        raise NotImplementedError("mount_image method is not implemented")

    def file_is_present(self, file_path):
        """
        check if file specified via 'file_path' is present in the image

        :param file_path: str, path to the file
        :return: True if file exists, False if the file is missing
        """
        raise NotImplementedError("file_is_present method is not implemented")

    def directory_is_present(self, directory_path):
        """
        check if directory specified via 'directory_path' is present inside the image; this
        method raises ConuException if the path exists but is not a directory

        :param directory_path: str, directory to check
        :return: True if directory exists, False if directory does not exist
        """
        raise NotImplementedError("directory_is_present is not implemented")

    def get_selinux_context(self, file_path):
        """
        return a permissions for 'file_path'

        :param file_path: str, path to the file
        :return: str
        """
        raise NotImplementedError("get_selinux_context is not implemented")

    def mount(self, mount_point=None):
        """
        mount image filesystem

        :param mount_point: str, directory where the filesystem will be mounted
        :return: instance of Filesystem
        """
        raise NotImplementedError("mount is not implemented")

    def run_via_binary(self, *args, **kwargs):
        """
        create a container using this image and run it in the background; this method is useful
        to test real user scenarios when users invoke containers using binary and not an API

        :param image: instance of Image
        :return: instance of Container
        """
        raise NotImplementedError("run_via_binary method is not implemented")

    def run_via_api(self, container_params):
        """
        create a container using this image and run it in the background

        :param container_params: instance of ContainerParameters
        :return: instance of Container
        """
        raise NotImplementedError("run_via_api method is not implemented")

    def create_container(self, container_params):
        """
        create a container using this image

        :param container_params: instance of ContainerParameters
        :return: instance of Container
        """
        raise NotImplementedError("create_container method is not implemented")

    def run_in_pod(self, namespace="default"):
        """
        run image inside Kubernetes Pod
        :param namespace: str, name of namespace where pod will be created
        :return: Pod instance
        """
        raise NotImplementedError("run_in_pod is not implemented")


class S2Image:
    """
    Additional functionality related to s2i-enabled container images
    """

    def extend(self, source, new_image_name, s2i_args=None):
        """
        extend this s2i-enabled image using provided source, raises ConuException if
        `s2i build` fails

        :param source: str, source used to extend the image, can be path or url
        :param new_image_name: str, name of the new, extended image
        :param s2i_args: list of str, additional options and arguments provided to `s2i build`
        :return: S2Image instance
        """
        raise NotImplementedError("extend method is not implemented")

    def usage(self):
        """
        Provide output of `s2i usage`

        :return: str
        """
        raise NotImplementedError("usage method is not implemented")

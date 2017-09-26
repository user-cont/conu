"""
Abstract class definitions for files in containers.
"""

from conu.apidefs.container import Container
from conu.apidefs.image import Image


class File(object):
    """
    File class definition which contains abstract methods. The instances should call the
    constructor
    """
    def __init__(self, mount_dir):
        """
        :param mount_dir: str, directory for mounting container
        """
        self.container = None
        self.container_id = None
        self.image = None
        self.image_id = None
        self.mount_dir = mount_dir

    def mount_container(self, container, container_id):
        """
        mount a container to host system
        :param container: container
        :param container_id: str, unique identifier of this container
        :return: None
        """
        if not isinstance(container, Container):
            raise RuntimeError("container argument is not an instance of Container class")
        self.container = container
        self.container_id = container_id
        raise NotImplementedError("mount_container method is not implemented")

    def mount_image(self, image, image_id):
        """
        mount an image to host system
        :param image: image
        :param image_id: str, unique identifier of this image
        :return: None
        """
        if not isinstance(image, Image):
            raise RuntimeError("container argument is not an instance of Container class")
        self.image = image
        self.image_id = image_id
        raise NotImplementedError("mount_container method is not implemented")

    def file_is_present(self, file_path):
        """
        check if file 'file_path' is present in container

        :param file_path: str, path to the file
        :return: True if file exists, False if file does not exist
        """
        raise NotImplementedError("get_file method is not implemented")

    def directory_is_present(self, directory_name):
        """
        check if directory 'directory_name' is present in container

        :param directory_name: str, Directory to check
        :return: True if directory exists, False if directory does not exist
        """
        raise NotImplementedError("directory_is_present is not implemented")

    def get_permissions(self, file_path):
        """
        return a permissions for 'file_path'
        :param file_path: str, path to the file
        :return: str
        """

        raise NotImplementedError("get_permissions is not implemented")

    def get_selinux_context(self, file_path):
        """
        return a permissions for 'file_path'
        :param file_path: str, path to the file
        :return: str
        """

        raise NotImplementedError("get_selinux_context is not implemented")

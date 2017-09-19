# -*- coding: utf-8 -*-

import json

from conu.utils.core import run_cmd


class Image(object):
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

    @classmethod
    def load_from_file(cls, file_path):
        """
        load Image from provided tarball

        :param file_path: str, path to tar file
        :return: Image instance
        """
        raise NotImplementedError()

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
        """
        inspect this image and save the output

        :param force: bool, update the metadata with up to date content
        :return: dict
        """
        if force or not self.inspect_data:
            self.inspect_data = json.loads(run_cmd("docker image inspect %s" % self.full_name()))[0]
        return self.inspect_data

    @classmethod
    def rmi(cls, image, force=False):
        """
        remove selected image

        :param image: str, image name, example: "fedora:latest"
        :param force: bool, use '-f'
        :return: None
        """
        run_cmd("docker image remove %s%s" % ("-f " if force else "", image))

    def clean(self, force=False):
        images_to_remove = self.additional_names + [self.full_name()]
        for i in images_to_remove:
            Image.rmi(i, force=force)
        self.additional_names = []


class Container(object):
    def __init__(self, image, container_id):
        """

        :param image: Image instance
        """
        if not isinstance(image, Image):
            raise RuntimeError("image argument is not an instance of Image class")
        self.image = image
        self.container_id = container_id
        self._inspect_data = None

    def inspect(self, force=False):
        if force or not self._inspect_data:
            self._inspect_data = json.loads(
                run_cmd("docker container inspect %s" % self.container_id))[0]
        return self._inspect_data

    def is_running(self):
        return self.inspect(force=True)["State"]["Running"]

    def get_ip(self):
        return self.inspect()["NetworkSettings"]["IPAddress"]

    @classmethod
    def run_using_docker_client(cls, image, docker_run_params=None, command=None):
        """
        create container using provided image and run it in the background

        :param image: instance of Image
        :param docker_run_params: str, parameters to pass to `docker create` command,
                you should not supply binary name, command name, image name, detach option
        :param command: str, command to run (optional)
        :return: instance of Container
        """
        c = "docker container run -d"
        if docker_run_params:
            c += " %s" % docker_run_params
        c += " %s" % image.full_name()
        if command:
            c += " %s" % command
        container_id = run_cmd(c)
        return Container(image, container_id)

    @classmethod
    def create_using_docker_client(cls, image, docker_create_params=None, command=None):
        """
        create container using provided image

        :param image: instance of Image
        :param docker_create_params: str, parameters to pass to `docker create` command,
                you should not supply binary name, command name, image name
        :param command: str, command to run (optional)
        :return: instance of Container
        """
        c = "docker container create"
        if docker_create_params:
            c += " %s" % docker_create_params
        c += " %s" % image.full_name()
        if command:
            c += " %s" % command
        container_id = run_cmd(c)
        return Container(image, container_id)

    def start_using_docker_client(self):
        """
        start current container using docker binary
        :return: None
        """
        c = ["docker", "container", "start", self.container_id]
        run_cmd(c)

    def execute(self, command, shell=True, **kwargs):
        c = ["docker", "container", "exec", self.container_id]
        if shell:
            c += ["/bin/bash", "-c"]
        if isinstance(command, list):
            c += command
        elif isinstance(command, str):
            c.append(command)
        return run_cmd(c, **kwargs)

    def logs(self):
        """
        get logs from this container

        :return: str, stdout & stderr from the container
        """
        c = ["docker", "container", "logs", self.container_id]
        output = run_cmd(c)
        return output

    def stop(self):
        """
        stop this container

        :return: None
        """
        run_cmd("docker container stop %s" % self.container_id)

    def rm(self, force=False):
        """
        remove this container

        :param force: bool, use -f
        :return: None
        """
        run_cmd("docker container rm %s%s" % ("-f " if force else "", self.container_id))

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        run_cmd("docker cp %s %s:%s" % (src, self.container_id, dest))

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container to host system

        :param src: str, path to a file or a directory within container
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        run_cmd("docker cp %s:%s %s" % (self.container_id, src, dest))

    def read_file(self, file_path):
        """
        read file specified via 'file_path' and return its content

        :param file_path: str, path to the file to read
        :return: str (not bytes), content of the file
        """
        # since run_cmd does split, we need to wrap like this because the command
        # is actually being wrapped in bash -c -- time for a drink
        return self.execute(["cat", file_path], shell=False)

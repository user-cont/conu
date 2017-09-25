# -*- coding: utf-8 -*-

import json
import subprocess

from conu.utils.core import run_cmd, random_str, logger


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
            Image.rmi(i, force=force)
        self.additional_names = []


class Container(object):
    def __init__(self, image, tag=None):
        self.tag = tag or random_str()
        if not isinstance(image, Image):
            raise BaseException("Image is not instance of Image class")
        self.json = None
        self.image = image
        self.docker_id = None
        self.__occupied = False

    def get_tag_name(self):
        return self.tag

    def inspect(self, force=False):
        if force or not self.json:
            output = json.loads(run_cmd("docker container inspect %s" % self.tag))[0]
            self.json = output
            return output
        else:
            return self.json

    def check_running(self):
        inspect_out = self.inspect(force=True)["State"]
        if (inspect_out["Status"] == "running" and
                not inspect_out["Paused"] and
                not inspect_out["Dead"]):
            return True
        else:
            return False

    def get_ip(self):
        return self.inspect()["NetworkSettings"]["IPAddress"]

    # TODO: add create menthod

    def start(self, command="", docker_params="-it -d", **kwargs):
        if not self.docker_id:
            self.__occupied = True
            output = self.run(command, docker_params=docker_params, **kwargs)
            self.docker_id = output.split("\n")[-2].strip()
        else:
            raise BaseException("Container already running on background")

    def execute(self, command, shell=True, **kwargs):
        c = ["docker", "container", "exec", self.tag]
        if shell:
            c += ["/bin/bash", "-c"]
        if isinstance(command, list):
            c += command
        elif isinstance(command, str):
            c.append(command)
        return run_cmd(c, **kwargs)

    def run(self, command="", docker_params="", **kwargs):
        command = command.split(" ") if command else []
        additional_params = docker_params.split(" ") if docker_params else []
        cmdline = ["docker", "container", "run", "--name", self.tag] + additional_params + [self.image.full_name()] + command
        output = run_cmd(cmdline, **kwargs)
        if not self.__occupied:
            self.clean()
        return output

    def install_packages(self, packages, command="dnf -y install"):
        if packages:
            logger.debug("installing packages: %s " % packages)
            return self.execute("%s %s" % (command, packages))

    def stop(self):
        if self.docker_id and self.check_running():
            run_cmd("docker stop %s" % self.docker_id)
            self.docker_id = None

    def clean(self):
        self.stop()
        self.__occupied = False
        try:
            run_cmd("docker container rm %s" % self.tag)
        except subprocess.CalledProcessError:
            logger.warning("Container already removed")

    def copy_to(self, src, dest):
        run_cmd("docker cp %s %s:%s" % (src, self.tag, dest))

    def copy_from(self, src, dest):
        self.start()
        run_cmd("docker cp %s:%s %s" % (self.tag, src, dest))

    def read_file(self, file_path):
        """
        read file specified via 'file_path' and return its content

        :param file_path: str, path to the file to read
        :return: str (not bytes), content of the file
        """
        # since run_cmd does split, we need to wrap like this because the command
        # is actually being wrapped in bash -c -- time for a drink
        return self.execute(["cat", file_path], shell=False)

    def check_file_exists(self, filename):
        """
        Function checks if file exists in container

        :param filename: Specify filename to check in container
        :return: True if all files exists
                 False if at least one does not exist
        """
        found = True
        if filename:
            logger.debug("Check if %s file is present in container." % filename)
            ret_val = self.execute(["ls", filename], shell=False)
            logger.debug(ret_val.strip())
            if filename != ret_val.strip():
                found = False
                logger.debug("Filename %s is not present in container" % filename)
        else:
            found = False
        return found

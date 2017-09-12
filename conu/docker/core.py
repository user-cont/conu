# -*- coding: utf-8 -*-

import json
from conu.utils import *

class Image(object):
    def __init__(self, container, tag=None, random_name_size=10):
        self.tag = tag or random_str()
        self.original = container
        self.__import_container()
        self.json = None

    def __import_container(self):
        if ".tar" in self.original:
            run_cmd("docker image import %s %s" % (self.original, self.tag))
            self.original = self.tag
        else:
            if "docker=" in self.original or "docker:" in self.original:
                self.original = self.original[7:]
            else:
                run_cmd("docker image pull %s" % self.original)
            run_cmd("docker image tag %s %s" % (self.original, self.tag))

    def get_tag_name(self):
        return self.tag

    def get_image_name(self):
        return self.original

    def __str__(self):
        return self.tag

    def inspect(self, force=False):
        if force or not self.json:
            output = json.loads(run_cmd("docker image inspect %s" % self.tag))[0]
            self.json = output
            return output
        else:
            return self.json

    def clean(self, force=False):
        run_cmd("docker image remove %s" % self.tag)
        if force and self.tag != self.original:
            run_cmd("docker image remove %s" % self.original)


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
        json = self.inspect(force=True)["State"]
        if (json["Status"] == "running" and
                not json["Paused"] and
                not json["Dead"]):
            return True
        else:
            return False

    def get_ip(self):
        return self.inspect()["NetworkSettings"]["IPAddress"]

    def start(self, command="", docker_params="-it -d", **kwargs):
        if not self.docker_id:
            self.__occupied = True
            output = self.run(command, docker_params=docker_params, **kwargs)
            self.docker_id = output.split("\n")[-2].strip()
        else:
            raise BaseException("Container already running on background")

    def execute(self, command, **kwargs):
        return run_cmd(["docker", "container", "exec", self.tag, "/bin/bash", "-c", command], **kwargs)

    def run(self, command="", docker_params="", **kwargs):
        command = command.split(" ") if command else []
        additional_params = docker_params.split(" ") if docker_params else []
        cmdline=["docker", "container", "run","--name", self.tag] + additional_params + [self.image.tag] + command
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



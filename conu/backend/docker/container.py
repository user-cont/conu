"""
Implementation of a docker container
"""

import json
import logging
import subprocess

from .image import DockerImage
from conu.apidefs.container import Container
from conu.utils.core import run_cmd, random_str

logger = logging.getLogger(__name__)


class DockerContainer(Container):
    def __init__(self, image, tag=None):
        super(DockerContainer, self).__init__(image, None)
        self.tag = tag or random_str()
        if not isinstance(image, DockerImage):
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
        i = self.inspect(force=True)

        # # TODO: kick-off of https://github.com/fedora-modularity/conu/issues/24
        # import pprint
        # pprint.pprint(i)
        # cmdline = ["docker", "container", "logs", self.tag]
        # output = run_cmd(cmdline)
        # print(output)

        inspect_out = i["State"]
        if (inspect_out["Status"] == "running" and
                not inspect_out["Paused"] and
                not inspect_out["Dead"]):
            return True
        else:
            return False

    def get_IPv4s(self):
        """
        Return all knwon IPv4 addresses of this container. It may be possible
        that the container has disabled networking: in that case, the list is
        empty

        :return: list of str
        """
        # FIXME: be graceful in obtaining values from dict: the keys might not be set
        return [x["IPAddress"]
                for x in self.inspect(force=False)["NetworkSettings"]["Networks"].values()]

    def get_ports(self):
        """
        get ports specified in container metadata

        :return: list of str
        """
        ports = []
        for p in self.inspect(force=False)["NetworkSettings"]["Ports"]:
            # TODO: gracefullness, error handling
            ports.append(p.split("/")[0])
        return ports

    def start(self, command="", docker_params="-it -d", **kwargs):
        if not self.docker_id:
            self.__occupied = True
            output = self.run(command, docker_params=docker_params, **kwargs)
            self.docker_id = output.split("\n")[-2].strip()
        else:
            raise BaseException("Container already running on background")

    def execute(self, command, shell=True, **kwargs):
        """
        execute a command in this container -- the container needs to be running

        :param command: str, command to execute in the container
        :param shell: bool, invoke the command in shell via '/bin/bash -c'
        :return: str (output) or Popen instance
        """
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
        cmdline = ["docker", "container", "run", "--name", self.tag] + additional_params + \
                  [self.image.full_name()] + command
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
            logger.warning("container already removed")

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

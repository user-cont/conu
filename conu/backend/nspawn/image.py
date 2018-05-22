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
Utilities related to manipulate nspawn images.
"""

import logging
import os
import enum
import hashlib
import glob
import subprocess
import time
from copy import deepcopy

from conu.backend.nspawn import constants
from conu.backend.nspawn.container import NspawnContainer
from conu.apidefs.filesystem import Filesystem
from conu.apidefs.image import Image
from conu.exceptions import ConuException
from conu.utils import run_cmd, random_str, convert_kv_to_dict, mkstemp, mkdtemp, command_exists
from conu.utils.filesystem import Volume

logger = logging.getLogger(__name__)


class NspawnImageFS(Filesystem):

    def __init__(self, image, mount_point=None):
        """
        Raises CommandDoesNotExistException if the command is not present on the system.

        :param image: instance of NspawnImage
        :param mount_point: str, directory where the filesystem will be mounted
        """
        self.system_requirements()
        self.mount_point_exists = False
        super(NspawnImageFS, self).__init__(image, mount_point=mount_point)
        self.image = image

    @staticmethod
    def system_requirements():
        """
        Check if all necessary packages are installed on system

        :return: None or raise exception if some tooling is missing
        """
        command_exists("losetup",
            ["losetup", "-V"],
            "losetup is not present on your system")
        command_exists(
            "partprobe",
            ["partprobe", "-v"],
            "partprobe is not present on your system")
        command_exists(
            "mount",
            ["mount", "-V"],
            "mount is not present on your system")

    def __enter__(self):
        # TODO RFE: use libguestfs if possible
        # TODO: allow pass partition number to mount exact partition of disc
        self.loopdevice = run_cmd(
            ["losetup", "--show", "-f", self.image.get_metadata()["Path"]],
            return_output=True).strip()
        run_cmd(["partprobe", self.loopdevice])
        partitions = glob.glob("{}*".format(self.loopdevice))
        for part in partitions:
            try:
                run_cmd(["mount", part, self.mount_point])
                return super(NspawnImageFS, self).__enter__()
            except Exception as e:
                logger.debug(
                    ConuException(
                        "unable to mount partition {}".format(part),
                        e))

    def __exit__(self, exc_type, exc_val, exc_tb):
        run_cmd(["umount", self.mount_point])
        run_cmd(["losetup", "-d", self.loopdevice])
        return super(NspawnImageFS, self).__exit__(exc_type, exc_val, exc_tb)


class ImagePullPolicy(enum.Enum):
    """
    This Enum defines the policy for pulling the docker images. The pull operation happens when
    creating an instance of a docker image. Supported values:

    * NEVER - do not pull the image
    * IF_NOT_PRESENT - pull it only if the image is not present
    * ALWAYS - always initiate the pull process - the image is being pulled even if it's present
      locally. It means that it may be overwritten by a remote counterpart or there may
      be a exception being raised if no such image is present in the registry.
    """
    # TODO: move this code to API, will be same for various backends
    NEVER = 0
    IF_NOT_PRESENT = 1
    ALWAYS = 2


class NspawnImage(Image):
    """
    Utility functions for nspawn images.
    """
    special_separator = "_"

    def __init__(self, repository, tag=None, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                 location=None):
        """
        :param repository: str, expected name of this image
        :param tag: not used, nspawn doesn't utilize the concept of tags
        :param pull_policy: enum, strategy to apply for pulling the image
        :param location: str, location from which we can obtain the image, it can be local (a
                path) or remote (URL)
        """
        self.system_requirements()
        self.container_process = None

        super(NspawnImage, self).__init__(repository, tag=None)
        if not isinstance(pull_policy, ImagePullPolicy):
            raise ConuException(
                "'pull_policy' is not an instance of ImagePullPolicy")
        self.pull_policy = pull_policy
        self.location = location
        # TODO: move this code to API __init__, will be same for various
        # backends or maybe add there some callback method
        if self.pull_policy == ImagePullPolicy.ALWAYS:
            logger.debug("pull policy set to 'always', pulling the image")
            self.pull()
        elif self.pull_policy == ImagePullPolicy.IF_NOT_PRESENT and not self.is_present():
            logger.debug(
                "pull policy set to 'if_not_present' and image is not present, "
                "pulling the image")
            self.pull()
        elif self.pull_policy == ImagePullPolicy.NEVER:
            logger.debug("pull policy set to 'never'")

    @staticmethod
    def system_requirements():
        """
        Check if all necessary packages are installed on system

        :return: None or raise exception if some tooling is missing
        """
        command_exists("systemd-nspawn",
            ["systemd-nspawn", "--version"],
            "Command systemd-nspawn does not seems to be present on your system"
            "Do you have system with systemd")
        command_exists(
            "machinectl",
            ["machinectl", "--no-pager", "--help"],
            "Command machinectl does not seems to be present on your system"
            "Do you have system with systemd")
        if "Enforcing" in run_cmd(["getenforce"], return_output=True, ignore_status=True):
            logger.error("Please disable selinux (setenforce 0), selinux blocks some nspawn operations"
                         "This may lead to strange behaviour")

    def __repr__(self):
        # TODO: move this method to api somehow? similar to docker
        return "NspawnImage(repository=%s, location=%s)" % (self.name, self.location)

    def __str__(self):
        # TODO: move to API it is same
        return self.get_full_name()

    def get_full_name(self):
        # TODO: move to API it is same
        """
        Provide full, complete image name

        :return: str
        """
        return self.name

    def _is_local(self):
        """
        Internal function
        check if repository in constructor is local file

        :return: bool
        """
        return os.path.exists(self.location)

    def get_id(self):
        """
        get unique identifier of this image

        :return: str
        """
        return self.name

    def _generate_id(self):
        """ create new unique identifier """
        name = self.name.replace(self.special_separator, "-").replace(".", "-")
        loc = "\/"
        if self.location:
            loc = self.location
        _id = "{PREFIX}{SEP}{NAME}{HASH}{SEP}".format(
            PREFIX=constants.CONU_ARTIFACT_TAG,
            NAME=name,
            HASH=hashlib.sha512(loc).hexdigest()[: 10],
            SEP=self.special_separator
        )
        return _id

    def is_present(self):
        """
        Check if image is already imported in images

        :return: bool
        """
        cmd = ["machinectl", "--no-pager", "image-status", self.name]
        try:
            run_cmd(cmd, return_output=True)  # ditch output
            return True
        except subprocess.CalledProcessError as ex:
            logger.info("nspawn image %s is not present probably: %s",
                        self.name, ex.output)
            return False

    def pull(self):
        """
        Pull this image from URL. Raises an exception if the image is not found in
        the registry.

        :return: None
        """
        ident = self.get_id()
        try:
            if self._is_local():
                logger.debug(
                    "Try to pull local file: {} -> {}".format(self.name, ident))
                run_cmd(["machinectl", "--no-pager", "--verify=no",
                         "import-raw", self.location, ident])
            else:
                logger.debug(
                    "Try to pull URL: {} -> {}".format(self.name, ident))
                run_cmd(["machinectl", "--no-pager", "--verify=no",
                         "pull-raw", self.location, ident])
                # add sleep after pull-raw to ensure, kernel finished all file ops, and original file is not blocked
                time.sleep(constants.DEFAULT_SLEEP)
        except ValueError as error:
            raise ConuException(
                "There was an error while pulling the image %s: %s",
                self.name,
                error)

    def create_snapshot(self, name, tag):
        """
        Create new instance of image with snaphot image (it is copied inside class constructuor)

        :param name: str - name of image - not used now
        :param tag: str - tag for image
        :return: NspawnImage instance
        """
        source = self.get_metadata()["Path"]
        logger.debug("Create Snapshot: %s -> %s" % (source, name))
        # FIXME: actually create the snapshot via clone command
        if name and tag:
            output_tag = "{}:{}".format(name, tag)
        else:
            output_tag = name or tag
        return self.__class__(repository=source, tag=output_tag)

    def tag_image(self, tag):
        """
        New instance of Image with another tag based on original image (tag will be appended)

        :param tag: std
        :return: NspawnImage instance
        """
        return self.create_snapshot(name=None, tag=tag)

    def inspect(self, refresh=True):
        """
        return cached metadata by default (a convenience method)

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        # TODO: move to API it is same
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
                raise ConuException(
                    "This image does not have a valid identifier.")
            self._metadata = convert_kv_to_dict(
                run_cmd(
                    ["machinectl", "--no-pager", "--output=export", "show-image", ident],
                    return_output=True))
        return self._metadata

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID, not used now
        :return: None
        """
        return run_cmd(["machinectl", "--no-pager", "remove", self.get_id()])

    def mount(self, mount_point=None):
        """
        mount image filesystem

        :param mount_point: str, directory where the filesystem will be mounted
        :return: instance of NspawnImageFS
        """
        return NspawnImageFS(self, mount_point=mount_point)

    def _wait_for_machine_finish(self, name):
        """
        Interna method
        wait until machine is really destroyed, machine does not exist.
        :param name: str machine name
        :return: True or exception
        """
        # TODO: rewrite it using probes module in utils
        for foo in range(constants.DEFAULT_RETRYTIMEOUT):
            time.sleep(constants.DEFAULT_SLEEP)
            out = run_cmd(
                ["machinectl", "--no-pager", "status", name],
                ignore_status=True, return_output=True)
            if out != 0:
                return True
        raise ConuException(
            "Unable to stop machine %s within %d" %
            (name, constants.DEFAULT_RETRYTIMEOUT))

    def run_via_binary(self, command=None, foreground=False, volumes=None,
            additional_opts=None, default_options=None, name=None, *args, **kwargs):
        """
        Create new instance NspawnContianer in case of not running at foreground, in case foreground run, return process
        object

        :param command: list - command to run
        :param foreground: bool - run process at foreground
        :param volumes: list - put additional bind mounts
        :param additional_opts: list of more boot options for systemd-nspawn command
        :param default_options: default boot option (-b)
        :param name: str - name of running instance
        :param args: pass thru params to subprocess.Popen
        :param kwargs: pass thru params to subprocess.Popen
        :return: process or NspawnContianer instance
        """
        command = deepcopy(command) or []
        volumes = deepcopy(volumes) or []
        additional_opts = deepcopy(additional_opts) or []
        internalkw = deepcopy(kwargs) or {}
        inernalargs = deepcopy(args) or []
        if default_options is None:
            default_options = ["-b"]
        # TODO: reconsile parameters (changed from API definition)
        logger.info("run container via binary in background")
        machine_name = constants.CONU_ARTIFACT_TAG
        if name:
            machine_name += name
        else:
            machine_name += random_str()

        if not foreground:
            # WARN: avoid to run boot without stderr and stdout to terminal, it breaks terminal,
            # it systemd-nspawn does some magic with console
            # TODO: is able to avoid this behaviour in better way?
            internalkw["stdout"] = subprocess.PIPE
            internalkw["stderr"] = subprocess.PIPE
        additional_opts += default_options
        if volumes:
            additional_opts += self.get_volume_options(volumes=volumes)
        logger.debug("starting NSPAWN")
        systemd_command = [
            "systemd-nspawn",
            "--machine",
            machine_name,
            "-i",
            self.get_metadata()["Path"]] + additional_opts + command
        logger.debug("Start command: %s" % " ".join(systemd_command))
        callback_method = (subprocess.Popen, systemd_command, inernalargs, internalkw)
        self.container_process = NspawnContainer.internal_run_container(
            name=machine_name,
            callback_method=callback_method,
            foreground=foreground
        )
        if foreground:
            return self.container_process
        else:
            return NspawnContainer(self, None, name=machine_name,
                                   start_process=self.container_process, start_action=callback_method)

    def run_foreground(self, *args, **kwargs):
        """
        Force to run process at foreground
        :param args: pass args to run command
        :param kwargs: pass args to run command
        :return:  process or NspawnContianer instance
        """
        return self.run_via_binary(foreground=True, default_options=[], *args, **kwargs)

    @staticmethod
    def get_volume_options(volumes):
        """
        Generates volume options to run methods.

        :param volumes: tuple or list of tuples in form target x source,target x source,target,mode.
        :return: list of the form ["--bind", "/source:/target", "--bind", "/other/source:/destination:z", ...]
        """
        if not isinstance(volumes, list):
            volumes = [volumes]
        volumes = [Volume.create_from_tuple(v) for v in volumes]
        result = []
        for v in volumes:
            result += ["--bind", str(v)]
        return result

    @staticmethod
    def bootstrap(
            repositories, name, packages=None, additional_packages=None,
            tag="latest", prefix=constants.CONU_ARTIFACT_TAG, packager=None):
        """
        bootstrap Image from scratch. It creates new image based on giver dnf repositories and package setts

        :param repositories:list of repositories
        :param packages: list of base packages in case you don't want to use base packages defined in contants
        :param additional_packages: list of additonal packages
        :param tag: tag the output image
        :param prefix: use some prefix for newly cretaed image (internal usage)
        :param packager: use another packages in case you dont want to use defined in constants (dnf)
        :return: NspawnImage instance
        """
        additional_packages = additional_packages or []
        if packages is None:
            packages = constants.CONU_NSPAWN_BASEPACKAGES
        package_set = packages + additional_packages
        if packager is None:
            packager = constants.BOOTSTRAP_PACKAGER
        mounted_dir = mkdtemp()
        if not os.path.exists(mounted_dir):
            os.makedirs(mounted_dir)
        imdescriptor, tempimagefile = mkstemp()
        image_size = constants.BOOTSTRAP_IMAGE_SIZE_IN_MB
        # create no partitions when create own image
        run_cmd(["dd", "if=/dev/zero", "of={}".format(tempimagefile),
                 "bs=1M", "count=1", "seek={}".format(image_size)])
        run_cmd([constants.BOOTSTRAP_FS_UTIL, tempimagefile])
        # TODO: is there possible to use NspawnImageFS class instead of direct
        # mount/umount, image objects does not exist
        run_cmd(["mount", tempimagefile, mounted_dir])
        if os.path.exists(os.path.join(mounted_dir, "usr")):
            raise ConuException("Directory %s already in use" % mounted_dir)
        if not os.path.exists(mounted_dir):
            os.makedirs(mounted_dir)
        repo_params = []
        repo_file_content = ""
        for cnt in range(len(repositories)):
            repo_params += ["--repofrompath",
                            "{0}{1},{2}".format(prefix, cnt, repositories[cnt])]
            repo_file_content += """
[{NAME}{CNT}]
name={NAME}{CNT}
baseurl={REPO}
enabled=1
gpgcheck=0
""".format(NAME=prefix, CNT=cnt, REPO=repositories[cnt])
        packages += set(additional_packages)
        logger.debug("Install system to direcory: %s" % mounted_dir)
        logger.debug("Install packages: %s" % packages)
        logger.debug("Repositories: %s" % repositories)
        packager_addition = [
            "--installroot",
            mounted_dir,
            "--disablerepo",
            "*",
            "--enablerepo",
            prefix + "*"]
        final_command = packager + packager_addition + repo_params + package_set
        try:
            run_cmd(final_command)
        except Exception as e:
            raise ConuException("Unable to install packages via command: {} (original exception {})".format(final_command, e))
        insiderepopath = os.path.join(
            mounted_dir,
            "etc",
            "yum.repos.d",
            "{}.repo".format(prefix))
        if not os.path.exists(os.path.dirname(insiderepopath)):
            os.makedirs(os.path.dirname(insiderepopath))
        with open(insiderepopath, 'w') as f:
            f.write(repo_file_content)
        run_cmd(["umount", mounted_dir])
        # add sleep before umount, to ensure, that kernel finish ops
        time.sleep(constants.DEFAULT_SLEEP)
        nspawnimage = NspawnImage(repository=name, location=tempimagefile, tag=tag)
        os.remove(tempimagefile)
        os.rmdir(mounted_dir)
        return nspawnimage
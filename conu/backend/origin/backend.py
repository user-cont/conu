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

import logging
import subprocess

from conu.backend.k8s.backend import K8sBackend
from conu.backend.docker.backend import DockerBackend
from conu.exceptions import ConuException
from conu.utils import oc_command_exists, run_cmd
from conu.backend.origin.constants import REGISTRY


logger = logging.getLogger(__name__)


# let this class inherit docstring from parent
class OpenshiftBackend(K8sBackend):

    def __init__(self, logging_level=logging.INFO, logging_kwargs=None):
        """
        This method serves as a configuration interface for conu.

        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        """
        super(OpenshiftBackend, self).__init__(
            logging_level=logging_level, logging_kwargs=logging_kwargs)

    def _oc_command(self, args):
        """
        return oc command to run

        :param args: list of str, arguments and options passed to oc binary
        :return: list of str
        """
        oc_command_exists()
        return ["oc"] + args

    def login_registry(self):
        """
        Login into docker daemon in OpenshiftCluster
        :return:
        """
        with DockerBackend() as backend:
            token = self.get_token()
            backend.login('developer', password=token, registry=REGISTRY, reauth=True)

    def get_token(self):
        """
        Get token of user logged in OpenShift cluster
        :return: str
        """
        try:
            return run_cmd(
                self._oc_command(["whoami", "-t"]), return_output=True).rstrip()  # remove '\n'
        except subprocess.CalledProcessError as ex:
            raise ConuException("oc whoami -t failed: %s" % ex)

    @staticmethod
    def push_to_registry(image, repository, tag, project):
        """
        :param image: DockerImage, image to push
        :param repository: str, new name of image
        :param tag: str, new tag of image
        :param project: str, oc project
        :return: DockerImage, new docker image
        """
        return image.push("%s/%s/%s" % (REGISTRY, project, repository), tag=tag)

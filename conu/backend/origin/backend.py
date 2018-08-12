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
This is backend for OpenShift
"""

import logging
import subprocess
import string
import random
import os.path
import requests

from requests.exceptions import ConnectionError

from conu.backend.k8s.backend import K8sBackend
from conu.backend.docker.backend import DockerBackend
from conu.exceptions import ConuException
from conu.utils import oc_command_exists, run_cmd
from conu.backend.origin.constants import REGISTRY
from conu.utils.http_client import get_url
from conu.utils.probes import Probe


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

        # provides HTTP client (requests.Session)
        self.http_session = requests.Session()

    def http_request(self, path="/", method="GET", host=None, port=None, json=False, data=None):
        """
        perform a HTTP request

        :param path: str, path within the reqest, e.g. "/api/version"
        :param method: str, HTTP method
        :param host: str, if None, set to 127.0.0.1
        :param port: str or int, if None, set to 8080
        :param json: bool, should we expect json?
        :param data: data to send (can be dict, list, str)
        :return: dict
        """

        host = host or '127.0.0.1'
        port = port or 8080
        url = get_url(host=host, port=port, path=path)

        return self.http_session.request(method, url, json=json, data=data)

    def _oc_command(self, args):
        """
        return oc command to run

        :param args: list of str, arguments and options passed to oc binary
        :return: list of str
        """
        oc_command_exists()
        return ["oc"] + args

    def new_app(self, image, source=None, template=None, name_in_template=None,
                other_images=None, oc_new_app_args=None, project=None):
        """
        Deploy app in OpenShift cluster using 'oc new-app'
        :param image: image to be used as builder image
        :param source: source used to extend the image, can be path or url
        :param template: str, url or local path to a template to use
        :param name_in_template: dict, {repository:tag} image name used in the template
        :param other_images: list of dict, some templates need other image to be pushed into the
               OpenShift registry, specify them in this parameter as list of dict [{<image>:<tag>}],
               where "<image>" is DockerImage and "<tag>" is a tag under which the image should be
               available in the OpenShift registry.
        :param oc_new_app_args: additional parameters for the `oc new-app`
        :param project: project where app should be created
        :return: str, name of app
        """

        if template is not None and source is not None:
            raise ConuException('cannot combine template parameter with source parameter')

        # app name is generated randomly
        random_string = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        name = 'app-{random_string}'.format(image=image.name, random_string=random_string)

        oc_new_app_args = oc_new_app_args or []

        if template is not None:
            if name_in_template is None:
                raise ConuException('You need to specify name_in_template')

            self._create_app_from_template(image, name, template, name_in_template,
                                           other_images, oc_new_app_args, project)

        else:
            new_image = OpenshiftBackend.push_to_registry(image, image.name.split('/')[-1],
                                                          image.tag, project)

            c = self._oc_command(
                ["new-app"] + oc_new_app_args + [new_image.name + "~" + source] +
                ["-n"] + [project] + ["--name=%s" % name])

            logger.info("Creating new app in project %s" % project)

            try:
                o = run_cmd(c, return_output=True)
                logger.debug(o)
            except subprocess.CalledProcessError as ex:
                raise ConuException("oc new-app failed: %s" % ex)

            if os.path.isdir(source):
                c = self._oc_command(["start-build"] + [name] + ["--from-dir=%s" % source])

                logger.info("Build application from local source in project %s", project)

                try:
                    o = run_cmd(c, return_output=True)
                    logger.debug(o)
                except subprocess.CalledProcessError as ex:
                    raise ConuException("oc start-build failed: %s" % ex)

        return name

    def _create_app_from_template(self, image, name, template, name_in_template,
                                  other_images, oc_new_app_args, project):
        """
        Helper function to create app from template
        :param image: image to be used as builder image
        :param template: str, url or local path to a template to use
        :param name_in_template: dict, {repository:tag} image name used in the template
        :param other_images: list of dict, some templates need other image to be pushed into the
               OpenShift registry, specify them in this parameter as list of dict [{<image>:<tag>}],
               where "<image>" is DockerImage and "<tag>" is a tag under which the image should be
               available in the OpenShift registry.
        :param oc_new_app_args: additional parameters for the `oc new-app`
        :param project: project where app should be created
        :return: None
        """
        # push images to registry
        repository, tag = list(name_in_template.items())[0]
        OpenshiftBackend.push_to_registry(image, repository, tag, project)

        other_images = other_images or []

        for o in other_images:
            image, tag = list(o.items())[0]
            OpenshiftBackend.push_to_registry(image, tag.split(':')[0], tag.split(':')[1],
                                              project)

        oc_new_app_args += ["-p", "NAME=%s" % name, "-p", "NAMESPACE=%s" % project]

        c = self._oc_command(["new-app"] + [template] + oc_new_app_args + ["-n"] + [project])

        logger.info("Creating new app in project %s" % project)

        try:
            # ignore status because sometimes oc new-app can fail when image
            # is already pushed in register
            o = run_cmd(c, return_output=True, ignore_status=True)
            logger.debug(o)
        except subprocess.CalledProcessError as ex:
            raise ConuException("oc new-app failed: %s" % ex)

        c = self._oc_command(["start-build"] + [name])

        logger.info("Build application from local source in project %s" % project)

        try:
            o = run_cmd(c, return_output=True)
            logger.debug(o)
        except subprocess.CalledProcessError as ex:
            raise ConuException("oc start-build failed: %s" % ex)

    def request_service(self, app_name, expected_output=None):
        """
        Make request on service of app. If there is connection error function return False.
        :param app_name: str, name of app
        :param expected_output: str, If not None method will check output returned from request
               and try to find matching string.
        :return: bool, True if connection was established False if there was connection error
        """
        ip = [service.get_ip() for service in self.list_services()
              if service.name == app_name][0]

        try:
            output = self.http_request(host=ip)
            if expected_output is not None:
                if expected_output not in output.text:
                    raise ConuException(
                        "Connection to service established, but didn't match expected output")
                else:
                    logger.info("Connection to service established and return expected output!")
            return True
        except ConnectionError:
            return False

    def wait_for_service(self, app_name, expected_output=None, timeout=100):
        """
        Block until service is not ready to accept requests,
        raises an exc ProbeTimeout if timeout is reached
        :param app_name: str, name of app
        :param expected_output: If not None method will check output returned from request
               and try to find matching string.
        :param timeout: int or float (seconds), time to wait for pod to run
        :return: None
        """
        logger.info('Waiting for service to get ready')
        Probe(timeout=timeout, fnc=self.request_service,
              app_name=app_name, expected_output=expected_output, expected_retval=True).run()

    def clean_project(self, app_name):
        """
        Delete all objects in current project in OpenShift cluster
        :return: None
        """
        logger.info('Deleting app')
        try:
            o = run_cmd(self._oc_command(["delete", "all", "-l app=%s" % app_name]),
                        return_output=True)
            o_lines = o.split('\n')
            for line in o_lines:
                logger.info(line)
        except subprocess.CalledProcessError as ex:
            raise ConuException("Cleanup failed: %s" % ex)

    def login_to_registry(self, username):
        """
        Login into docker daemon in OpenshiftCluster
        :return:
        """
        with DockerBackend() as backend:
            token = self.get_token()
            backend.login(username, password=token, registry=REGISTRY, reauth=True)

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

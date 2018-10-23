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
import os.path
import requests

from requests.exceptions import ConnectionError

from conu.backend.origin.registry import push_to_registry
from conu.backend.k8s.backend import K8sBackend
from conu.exceptions import ConuException
from conu.utils import oc_command_exists, run_cmd, random_str, check_port
from conu.utils.http_client import get_url
from conu.utils.probes import Probe, ProbeTimeout


logger = logging.getLogger(__name__)


# let this class inherit docstring from parent
class OpenshiftBackend(K8sBackend):

    def __init__(self, api_key=None, logging_level=logging.INFO, logging_kwargs=None):
        """
        This method serves as a configuration interface for conu.

        :param api_key: str, Bearer API token
        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        """
        super(OpenshiftBackend, self).__init__(api_key,
                                               logging_level=logging_level,
                                               logging_kwargs=logging_kwargs)

        # provides HTTP client (requests.Session)
        self.http_session = requests.Session()

    def http_request(self, path="/", method="GET", host=None, port=None, json=False, data=None):
        """
        perform a HTTP request

        :param path: str, path within the request, e.g. "/api/version"
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

    def deploy_image(self, image, oc_new_app_args, project, name=None):
        """
        Deploy image in OpenShift cluster using 'oc new-app'
        :param image: DockerImage, image to be deployed
        :param oc_new_app_args: additional parameters for the `oc new-app`, env variables etc.
        :param project: project where app should be created
        :param name:str, name of application, if None random name is generated
        :return: str, name of the app
        """

        # app name is generated randomly
        name = name or 'app-{random_string}'.format(random_string=random_str(5))

        oc_new_app_args = oc_new_app_args or []

        new_image = push_to_registry(image, image.name.split('/')[-1], image.tag, project)

        c = self._oc_command(
            ["new-app"] + oc_new_app_args + [new_image.name] +
            ["-n"] + [project] + ["--name=%s" % name])

        logger.info("Creating new app in project %s", project)

        try:
            run_cmd(c)
        except subprocess.CalledProcessError as ex:
            raise ConuException("oc new-app failed: %s" % ex)

        return name

    def create_new_app_from_source(self, image, project, source=None, oc_new_app_args=None):
        """
        Deploy app using source-to-image in OpenShift cluster using 'oc new-app'
        :param image: image to be used as builder image
        :param project: project where app should be created
        :param source: source used to extend the image, can be path or url
        :param oc_new_app_args: additional parameters for the `oc new-app`
        :return: str, name of the app
        """

        # app name is generated randomly
        name = 'app-{random_string}'.format(random_string=random_str(5))

        oc_new_app_args = oc_new_app_args or []

        new_image = push_to_registry(image, image.name.split('/')[-1], image.tag, project)

        c = self._oc_command(
            ["new-app"] + [new_image.name + "~" + source] + oc_new_app_args
            + ["-n"] + [project] + ["--name=%s" % name])

        logger.info("Creating new app in project %s", project)

        try:
            o = run_cmd(c, return_output=True)
            logger.debug(o)
        except subprocess.CalledProcessError as ex:
            raise ConuException("oc new-app failed: %s" % ex)

        # build from local source
        if os.path.isdir(source):
            self.start_build(name, ["-n", project, "--from-dir=%s" % source])

        return name

    def create_app_from_template(self, image, name, template, name_in_template,
                                 other_images, oc_new_app_args, project):
        """
        Helper function to create app from template
        :param image: image to be used as builder image
        :param name: name of app from template
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
        push_to_registry(image, repository, tag, project)

        other_images = other_images or []

        for o in other_images:
            image, tag = list(o.items())[0]
            push_to_registry(image, tag.split(':')[0], tag.split(':')[1], project)

        c = self._oc_command(["new-app"] + [template] + oc_new_app_args + ["-n"] + [project]
                             + ["--name=%s" % name])

        logger.info("Creating new app in project %s", project)

        try:
            # ignore status because sometimes oc new-app can fail when image
            # is already pushed in register
            o = run_cmd(c, return_output=True, ignore_status=True)
            logger.debug(o)
        except subprocess.CalledProcessError as ex:
            raise ConuException("oc new-app failed: %s" % ex)

        return name

    def start_build(self, build, args=None):
        """
        Start new build, raise exception if build failed
        :param build: str, name of the build
        :param args: list of str, another args of 'oc start-build' commands
        :return: None
        """

        args = args or []

        c = self._oc_command(["start-build"] + [build] + args)

        logger.info("Executing build %s", build)
        logger.info("Build command: %s", " ".join(c))

        try:
            Probe(timeout=-1, pause=5, count=2, expected_exceptions=subprocess.CalledProcessError,
                  expected_retval=None, fnc=run_cmd, cmd=c).run()
        except ProbeTimeout as e:
            raise ConuException("Cannot start build of application: %s" % e)

    def request_service(self, app_name, port, expected_output=None):
        """
        Make request on service of app. If there is connection error function return False.
        :param app_name: str, name of the app
        :param expected_output: str, If not None method will check output returned from request
               and try to find matching string.
        :param port: str or int, port of the service
        :return: bool, True if connection was established False if there was connection error
        """

        # get ip of service
        ip = [service.get_ip() for service in self.list_services()
              if service.name == app_name][0]

        # make http request to obtain output
        if expected_output is not None:
            try:
                output = self.http_request(host=ip, port=port)
                if expected_output not in output.text:
                    raise ConuException(
                        "Connection to service established, but didn't match expected output")
                else:
                    logger.info("Connection to service established and return expected output!")
                    return True
            except ConnectionError as e:
                logger.info("Connection to service failed %s!", e)
                return False
        elif check_port(port, host=ip):  # check if port is open
            return True

        return False

    def wait_for_service(self, app_name, port, expected_output=None, timeout=100):
        """
        Block until service is not ready to accept requests,
        raises an exc ProbeTimeout if timeout is reached
        :param app_name: str, name of the app
        :param port: str or int, port of the service
        :param expected_output: If not None method will check output returned from request
               and try to find matching string.
        :param timeout: int or float (seconds), time to wait for pod to run
        :return: None
        """
        logger.info('Waiting for service to get ready')
        try:

            Probe(timeout=timeout, pause=10, fnc=self.request_service, app_name=app_name,
                  port=port, expected_output=expected_output, expected_retval=True).run()
        except ProbeTimeout:
            logger.warning("Timeout: Request to service unsuccessful.")
            raise ConuException("Timeout: Request to service unsuccessful.")

    def all_pods_are_ready(self, app_name):
        """
        Check if all pods are ready for specific app
        :param app_name: str, name of the app
        :return: bool
        """
        app_pod_exists = False
        for pod in self.list_pods():
            if app_name in pod.name and 'build' not in pod.name and 'deploy' not in pod.name:
                app_pod_exists = True
                if not pod.is_ready():
                    return False
        if app_pod_exists:
            logger.info("All pods are ready!")
            return True

        return False

    def get_status(self):
        """
        Get status of OpenShift cluster, similar to `oc status`
        :return: str
        """
        try:
            c = self._oc_command(["status"])
            o = run_cmd(c, return_output=True)
            for line in o.split('\n'):
                logger.debug(line)
            return o
        except subprocess.CalledProcessError as ex:
            raise ConuException("Cannot obtain OpenShift cluster status: %s" % ex)

    def get_logs(self, name):
        """
        Obtain cluster status and logs from all pods and print them using logger.
        This method is useful for debugging.
        :param name: str, name of app generated by oc new-app
        :return: str, cluster status and logs from all pods
        """
        logs = self.get_status()

        for pod in self.list_pods():
            if name in pod.name:  # get just logs from pods related to app
                pod_logs = pod.get_logs()
                if pod_logs:
                    logs += pod_logs

        return logs

    def clean_project(self, app_name=None, delete_all=False):
        """
        Delete objects in current project in OpenShift cluster. If both parameters are passed,
        delete all objects in project.
        :param app_name: str, name of app
        :param delete_all: bool, if true delete all objects in current project
        :return: None
        """

        if not app_name and not delete_all:
            ConuException("You need to specify either app_name or set delete_all=True")

        if delete_all:
            args = ["--all"]
            logger.info('Deleting all objects in current project')
        else:
            args = "-l app=%s" % app_name
            logger.info('Deleting all objects with label app=%s', app_name)

        try:
            o = run_cmd(self._oc_command(["delete", "all", args]),
                        return_output=True)
            o_lines = o.split('\n')
            for line in o_lines:
                logger.info(line)
        except subprocess.CalledProcessError as ex:
            raise ConuException("Cleanup failed because of exception: %s" % ex)

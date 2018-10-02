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
This are the methods helpful while working with OpenShift internal docker registry
"""
import logging

from conu.backend.origin.constants import INTERNAL_REGISTRY_PORT
from conu.backend.docker.backend import DockerBackend
from conu.utils import get_oc_api_token
import conu.backend.origin.backend

logger = logging.getLogger(__name__)


def login_to_registry(username, token=None):
    """
    Login within docker daemon to docker registry running in this OpenShift cluster
    :return:
    """

    token = token or get_oc_api_token()

    with DockerBackend() as backend:
        backend.login(username, password=token,
                      registry=get_internal_registry_ip(), reauth=True)


def push_to_registry(image, repository, tag, project):
    """
    :param image: DockerImage, image to push
    :param repository: str, new name of image
    :param tag: str, new tag of image
    :param project: str, oc project
    :return: DockerImage, new docker image
    """
    return image.push("%s/%s/%s" % (get_internal_registry_ip(), project, repository), tag=tag)


def get_internal_registry_ip():
    """
    Search for `docker-registry` IP
    :return: str, ip address
    """
    with conu.backend.origin.backend.OpenshiftBackend() as origin_backend:
        services = origin_backend.list_services()
        for service in services:
            if service.name == 'docker-registry':
                logger.debug("Internal docker-registry IP: %s",
                             "{ip}:{port}".format(ip=service.get_ip(), port=INTERNAL_REGISTRY_PORT))
                return "{ip}:{port}".format(ip=service.get_ip(), port=INTERNAL_REGISTRY_PORT)
    return None

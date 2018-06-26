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

import string
import random

from conu.apidefs.backend import Backend
from conu.backend.k8s.pod import Pod
from conu.backend.k8s.service import Service
from conu.backend.k8s.deployment import Deployment
from conu.backend.k8s.utils import k8s_ports_to_metadata_ports
from conu.apidefs.metadata import ImageMetadata
from conu.backend.k8s.client import get_core_api, get_apps_api

from kubernetes import client


# let this class inherit docstring from parent
class K8sBackend(Backend):

    def __init__(self, logging_level=logging.INFO, logging_kwargs=None):
        """
        This method serves as a configuration interface for conu.

        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        :param cleanup: list, list of cleanup policy values, examples:
            - [CleanupPolicy.EVERYTHING]
            - [CleanupPolicy.VOLUMES, CleanupPolicy.TMP_DIRS]
            - [CleanupPolicy.NOTHING]
        """
        super(K8sBackend, self).__init__(
            logging_level=logging_level, logging_kwargs=logging_kwargs)

        self.core_api = get_core_api()
        self.apps_api = get_apps_api()

    def list_pods(self):
        """
        List all available pods.

        :return: collection of instances of :class:`conu.backend.k8s.pod.Pod`
        """

        return [Pod(name=p.metadata.name, namespace=p.metadata.namespace, spec=p.spec)
                for p in self.core_api.list_pod_for_all_namespaces(watch=False).items]

    def list_services(self):
        """
        List all available services.

        :return: collection of instances of :class:`conu.backend.k8s.service.Service`
        """

        return [Service(name=s.metadata.name,
                        ports=k8s_ports_to_metadata_ports(s.spec.ports),
                        namespace=s.metadata.namespace,
                        labels=s.matadata.labels, selector=s.spec.selector)
                for s in self.core_api.list_service_for_all_namespaces(watch=False).items]

    def list_deployments(self):
        """
        List all available deployments.

        :return: collection of instances of :class:`conu.backend.k8s.deployment.Deployment`
        """

        return [Deployment(name=d.metadata.name,
                           namespace=d.metadata.namespace,
                           labels=d.matadata.labels, selector=d.spec.selector,
                           image_metadata=ImageMetadata())
                for d in self.core_api.list_deployment_for_all_namespaces(watch=False).items]

    def create_namespace(self):
        """
        Create namespace with random name
        :return: name of new created namespace
        """
        random_string = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(4))

        name = 'namespace-{random_string}'.format(random_string=random_string)

        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))

        self.core_api.create_namespace(namespace)

        return name

    def delete_namespace(self, name):
        """
        Delete namespace with specific name
        :param name: str, namespace to delete
        """
        self.core_api.delete_namespace(name, client.V1DeleteOptions())


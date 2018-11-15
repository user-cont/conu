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
This is backend for kubernetes
"""
import logging
import enum

from conu.apidefs.backend import Backend
from conu.backend.k8s.pod import Pod
from conu.backend.k8s.service import Service
from conu.backend.k8s.deployment import Deployment
from conu.backend.k8s.utils import k8s_ports_to_metadata_ports
from conu.apidefs.metadata import ImageMetadata
import conu.backend.k8s.client as k8s_client
from conu.exceptions import ConuException
from conu.utils.probes import Probe
from conu.utils import random_str

from kubernetes import client
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


# let this class inherit docstring from parent
class K8sBackend(Backend):

    def __init__(self, api_key=None, logging_level=logging.INFO, logging_kwargs=None, cleanup=None):
        """
        This method serves as a configuration interface for conu.

        :param api_key: str, Bearer API token
        :param logging_level: int, control logger verbosity: see logging.{DEBUG,INFO,ERROR}
        :param logging_kwargs: dict, additional keyword arguments for logger set up, for more info
                                see docstring of set_logging function
        :param cleanup: list, list of k8s cleanup policy values, examples:
            - [CleanupPolicy.EVERYTHING]
            - [CleanupPolicy.PODS, CleanupPolicy.SERVICES]
            - [CleanupPolicy.NOTHING]
        """
        super(K8sBackend, self).__init__(
            logging_level=logging_level, logging_kwargs=logging_kwargs)

        k8s_client.API_KEY = api_key
        self.core_api = k8s_client.get_core_api()
        self.apps_api = k8s_client.get_apps_api()

        self.managed_namespaces = []

        self.cleanup = cleanup or [K8sCleanupPolicy.NOTHING]

        if K8sCleanupPolicy.NOTHING in self.cleanup and len(self.cleanup) != 1:
            raise ConuException("Cleanup policy NOTHING cannot be combined with other values")

    def list_pods(self, namespace=None):
        """
        List all available pods.

        :param namespace: str, if not specified list pods for all namespaces
        :return: collection of instances of :class:`conu.backend.k8s.pod.Pod`
        """

        if namespace:
            return [Pod(name=p.metadata.name, namespace=namespace, spec=p.spec)
                    for p in self.core_api.list_namespaced_pod(namespace, watch=False).items]

        return [Pod(name=p.metadata.name, namespace=p.metadata.namespace, spec=p.spec)
                for p in self.core_api.list_pod_for_all_namespaces(watch=False).items]

    def list_services(self, namespace=None):
        """
        List all available services.

        :param namespace: str, if not specified list services for all namespaces
        :return: collection of instances of :class:`conu.backend.k8s.service.Service`
        """

        if namespace:
            return [Service(name=s.metadata.name,
                            ports=k8s_ports_to_metadata_ports(s.spec.ports),
                            namespace=s.metadata.namespace,
                            labels=s.metadata.labels, selector=s.spec.selector, spec=s.spec)
                    for s in self.core_api.list_namespaced_service(namespace, watch=False).items]

        return [Service(name=s.metadata.name,
                        ports=k8s_ports_to_metadata_ports(s.spec.ports),
                        namespace=s.metadata.namespace,
                        labels=s.metadata.labels, selector=s.spec.selector, spec=s.spec)
                for s in self.core_api.list_service_for_all_namespaces(watch=False).items]

    def list_deployments(self, namespace=None):
        """
        List all available deployments.

        :param namespace: str, if not specified list deployments for all namespaces
        :return: collection of instances of :class:`conu.backend.k8s.deployment.Deployment`
        """

        if namespace:
            return [Deployment(name=d.metadata.name,
                               namespace=d.metadata.namespace,
                               labels=d.metadata.labels, selector=d.spec.selector,
                               image_metadata=ImageMetadata(
                                   name=d.spec.template.spec.containers[0].name.split("-", 1)[0]))
                    for d in self.apps_api.list_namespaced_deployment(namespace, watch=False).items]

        return [Deployment(name=d.metadata.name,
                           namespace=d.metadata.namespace,
                           labels=d.metadata.labels, selector=d.spec.selector,
                           image_metadata=ImageMetadata(
                               name=d.spec.template.spec.containers[0].name.split("-", 1)[0]))
                for d in self.apps_api.list_deployment_for_all_namespaces(watch=False).items]

    def create_namespace(self):
        """
        Create namespace with random name
        :return: name of new created namespace
        """
        name = 'namespace-{random_string}'.format(random_string=random_str(5))

        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))

        self.core_api.create_namespace(namespace)

        logger.info("Creating namespace: %s", name)

        # save all namespaces created with this backend
        self.managed_namespaces.append(name)

        # wait for namespace to be ready
        Probe(timeout=30, pause=5, expected_retval=True,
              fnc=self._namespace_ready, namespace=name).run()

        return name

    def _namespace_ready(self, namespace):
        """
        Check if API tokens for service accounts are generated
        :param namespace: str, namespace
        :return: bool
        """
        try:
            secrets = self.core_api.list_namespaced_secret(namespace=namespace)
            if len(secrets.items) > 0:
                # API tokens for service accounts are generated
                logger.info("Namespace is ready!")
                return True
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API %s\n" % e)

        return False

    def delete_namespace(self, name):
        """
        Delete namespace with specific name
        :param name: str, namespace to delete
        :return: None
        """
        self.core_api.delete_namespace(name, client.V1DeleteOptions())

        logger.info("Deleting namespace: %s", name)

    def _clean(self):
        """
        Method for cleaning according to object cleanup policy value
        :return: None
        """
        if K8sCleanupPolicy.NAMESPACES in self.cleanup:
            self.cleanup_namespaces()
        elif K8sCleanupPolicy.EVERYTHING in self.cleanup:
            self.cleanup_pods()
            self.cleanup_services()
            self.cleanup_deployments()
        else:
            if K8sCleanupPolicy.PODS in self.cleanup:
                self.cleanup_pods()
            if K8sCleanupPolicy.SERVICES in self.cleanup:
                self.cleanup_services()
            if K8sCleanupPolicy.DEPLOYMENTS in self.cleanup:
                self.cleanup_deployments()

    def cleanup_namespaces(self):
        """
        Delete all namespaces created by this backend
        :return: None
        """
        for namespace in self.managed_namespaces:
            self.delete_namespace(namespace)

    def cleanup_pods(self):
        """
        Delete all pods created in namespaces associated with this backend
        :return: None
        """
        pods = self.list_pods()

        for pod in pods:
            if pod.namespace in self.managed_namespaces:
                pod.delete()

    def cleanup_services(self):
        """
        Delete all services created in namespaces associated with this backend
        :return: None
        """
        services = self.list_services()

        for service in services:
            if service.namespace in self.managed_namespaces:
                service.delete()

    def cleanup_deployments(self):
        """
        Delete all deployments created in namespaces associated with this backend
        :return: None
        """
        deployments = self.list_deployments()

        for deployment in deployments:
            if deployment.namespace in self.managed_namespaces:
                deployment.delete()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._clean()


class K8sCleanupPolicy(enum.Enum):
    """
    This Enum defines the policy for cleanup.

    * NOTHING - clean nothing
    * EVERYTHING - delete just objects in all namespaces
        associated with this backend - (pods, service, deployments)
    * NAMESPACES - delete all namespaces associated with this backend and
        objects in these namespaces (pods, service, deployments)
    * PODS - delete all pods in namespaces associated with this backend
    * SERVICES - delete all services in namespaces associated with this backend
    * DEPLOYMENTS - delete all deployments in namespaces associated with this backend
    """

    NOTHING = 0
    EVERYTHING = 1
    NAMESPACES = 2
    PODS = 3
    SERVICES = 4
    DEPLOYMENTS = 5

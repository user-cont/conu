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
Implementation of a Kubernetes deployment
"""

import logging

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from conu.utils.probes import Probe
from conu.backend.k8s.pod import Pod
from conu.exceptions import ConuException

config.load_kube_config()
api = client.AppsV1Api()

logger = logging.getLogger(__name__)


class Deployment(object):

    def __init__(self, name, selector, labels, image_metadata, namespace='default',
                 create_in_cluster=False):
        """
        Utility functions for kubernetes deployments.

        :param name: str, name of the deployment
        :param selector: Label selector for pods. Existing ReplicaSets whose pods are selected by
         this will be the ones affected by this deployment. It must match the pod template's labels
        :param labels: dict, dict of labels
        :param image_metadata: ImageMetadata
        :param namespace: str, name of the namespace
        """
        self.name = name
        self.namespace = namespace

        self.pod = Pod.create(image_metadata)

        self.spec = client.V1DeploymentSpec(selector=client.V1LabelSelector(match_labels=selector),
                                            template=client.V1PodTemplateSpec(
                                                metadata=client.V1ObjectMeta(labels=selector),
                                                spec=self.pod.spec))

        self.metadata = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels=labels)

        self.body = client.V1Deployment(spec=self.spec, metadata=self.metadata)

        if create_in_cluster:
            self.create_in_cluster()

    def delete(self):
        """
        delete Deployment from the Kubernetes cluster
        :return: None
        """

        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_deployment(self.name, self.namespace, body)

            logger.info("Deleting Deployment %s in namespace: %s", self.name, self.namespace)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - delete_namespaced_deployment: %s\n" % e)

        if status.status == 'Failure':
            raise ConuException("Deletion of Deployment failed")

    def get_status(self):
        """
        get status of the Deployment
        :return: V1DeploymentStatus, https://git.io/vhKE3
        """
        try:
            api_response = api.read_namespaced_deployment_status(self.name, self.namespace)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - "
                "read_namespaced_deployment_status: %s\n" % e)

        return api_response.status

    def all_pods_ready(self):
        """
        Check if number of replicas with same selector is equals to number of ready replicas
        :return: bool
        """

        if self.get_status().replicas and self.get_status().ready_replicas:
            if self.get_status().replicas == self.get_status().ready_replicas:
                return True

        return False

    def wait(self, timeout=15):
        """
        block until all replicas are not ready, raises an exc ProbeTimeout if timeout is reached
        :param timeout: int or float (seconds), time to wait for pod to run
        :return: None
        """

        Probe(timeout=timeout, fnc=self.all_pods_ready, expected_retval=True).run()

    def create_in_cluster(self):

        try:
            api.create_namespaced_deployment(self.namespace, self.body)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - create_namespaced_deployment: %s\n" % e)

        logger.info("Creating Deployment %s in namespace: %s", self.name, self.namespace)

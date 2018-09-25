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
Implementation of a Kubernetes service
"""

import logging

from kubernetes import client
from kubernetes.client.rest import ApiException
from conu.exceptions import ConuException
from conu.backend.k8s.utils import metadata_ports_to_k8s_ports
from conu.backend.k8s.client import get_core_api

logger = logging.getLogger(__name__)


class Service(object):

    def __init__(self, name, ports, namespace='default', labels=None, selector=None,
                 create_in_cluster=False, spec=None):
        """
        Utility functions for kubernetes services.

        :param name: str, name of the service
        :param namespace: str, name of the namespace
        :param ports: list of str, list of exposed ports, example:
                - ['1234/tcp', '8080/udp']
        :param labels: dict, dict of labels
        :param selector: dict, route service traffic to pods with label keys and
            values matching this selector
        """
        self.name = name
        self.namespace = namespace
        self.ports = ports

        exposed_ports = metadata_ports_to_k8s_ports(self.ports)

        self.metadata = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels=labels)
        self.spec = spec or client.V1ServiceSpec(ports=exposed_ports, selector=selector)

        self.body = client.V1Service(spec=self.spec, metadata=self.metadata)

        self.api = get_core_api()

        if create_in_cluster:
            self.create_in_cluster()

    def delete(self):
        """
        delete service from the Kubernetes cluster
        :return: None
        """

        body = client.V1DeleteOptions()

        try:
            status = self.api.delete_namespaced_service(self.name, self.namespace, body)

            logger.info(
                "Deleting Service %s in namespace: %s", self.name, self.namespace)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - delete_namespaced_service: {}\n".format(e))

        if status.status == 'Failure':
            raise ConuException("Deletion of Service failed")

    def get_status(self):
        """
        get status of service
        :return: V1ServiceStatus,
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ServiceStatus.md
        """

        try:
            api_response = self.api.read_namespaced_service_status(self.name, self.namespace)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - read_namespaced_service_status: %s\n" % e)

        return api_response.status

    def get_ip(self):
        """
        get IP adress of service
        :return: str, IP address
        """

        return self.spec.cluster_ip

    def create_in_cluster(self):
        """
        call Kubernetes API and create this Service in cluster,
        raise ConuExeption if the API call fails
        :return: None
        """
        try:
            self.api.create_namespaced_service(self.namespace, self.body)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - create_namespaced_service: {}\n".format(e))

        logger.info(
            "Creating Service %s in namespace: %s", self.name, self.namespace)

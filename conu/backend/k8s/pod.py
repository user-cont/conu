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
Implementation of a Kubernetes pod
"""

import logging
import enum
import random
import string
import getpass

from kubernetes import client
from kubernetes.client.rest import ApiException

from conu.utils.probes import Probe
from conu.exceptions import ConuException
from conu.backend.k8s.client import get_core_api


logger = logging.getLogger(__name__)


class Pod(object):

    def __init__(self, namespace, name=None, spec=None, from_template=None):
        """
        Utility functions for kubernetes pods.

        :param namespace: str, namespace in which is pod created
        :param name: name of pod
        :param spec: pod spec
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodSpec.md
        :param from_template: str, pod template, example:
               - https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/#pod-templates
        """
        self.core_api = get_core_api()
        self.namespace = namespace
        self.phase = None

        if (from_template is not None) and (name is not None or spec is not None):
            raise ConuException('from_template cannot be passed to constructor at the same time'
                                ' with name or spec')
        elif from_template is not None:  # create Pod from template
            try:
                pod_instance = self.core_api.create_namespaced_pod(namespace=namespace,
                                                                   body=from_template)
            except ApiException as e:
                raise ConuException(
                    "Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)

            logger.info(
                "Starting Pod %s in namespace %s" % (pod_instance.metadata.name, namespace))

            self.name = pod_instance.metadata.name
            self.spec = pod_instance.spec

        elif name is not None or spec is not None:
            self.name = name
            self.spec = spec
        else:
            raise ConuException('to create pod you need to specify pod template or'
                                ' properties: name and spec.')

    def delete(self):
        """
        delete pod from the Kubernetes cluster
        :return: None
        """
        body = client.V1DeleteOptions()

        try:
            status = self.core_api.delete_namespaced_pod(self.name, self.namespace, body)
            logger.info("Deleting Pod %s in namespace %s", self.name, self.namespace)
            self.phase = PodPhase.TERMINATING
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - delete_namespaced_pod: %s\n" % e)

        if status.status == 'Failure':
            raise ConuException("Deletion of Pod failed")

    def get_status(self):
        """

        get status of the Pod
        :return: V1PodStatus,
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodStatus.md
        """
        try:
            api_response = self.core_api.read_namespaced_pod_status(self.name, self.namespace)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - read_namespaced_pod_status: %s\n" % e)

        return api_response.status

    def get_ip(self):
        """
        get IP address of Pod
        :return: str, IP address or empty string if is not allocated yet
        """

        return self.get_status().pod_ip

    def get_logs(self):
        """
        print logs from pod
        :return: str or None
        """
        try:
            api_response = self.core_api.read_namespaced_pod_log(self.name, self.namespace)
            logger.debug("Logs from pod: %s in namespace: %s", self.name, self.namespace)
            for line in api_response.split('\n'):
                logger.debug(line)
            return api_response
        except ApiException as e:
            # no reason to throw exception when logs cannot be obtain, just notify user
            logger.debug("Cannot get pod logs because of "
                         "exception during calling Kubernetes API %s\n", e)

        return None

    def get_phase(self):
        """
        get phase of the pod
        :return: PodPhase enum

        """

        if self.phase != PodPhase.TERMINATING:
            self.phase = PodPhase.get_from_string(self.get_status().phase)

        return self.phase

    def get_conditions(self):
        """
        get conditions through which the pod has passed
        :return: list of PodCondition enum or empty list
        """

        # filter just values that are true (means that pod has that condition right now)
        return [PodCondition.get_from_string(c.type) for c in self.get_status().conditions
                if c.status == 'True']

    def is_ready(self):
        """
        Check if pod is in READY condition
        :return: bool
        """
        if PodCondition.READY in self.get_conditions():
            logger.info("Pod: %s in namespace: %s is ready!", self.name, self.namespace)
            return True
        return False

    def wait(self, timeout=15):
        """
        block until pod is not ready, raises an exc ProbeTimeout if timeout is reached
        :param timeout: int or float (seconds), time to wait for pod to run
        :return: None
        """

        Probe(timeout=timeout, fnc=self.is_ready, expected_retval=True).run()

    @staticmethod
    def create(image_data):
        """
        :param image_data: ImageMetadata
        :return: V1Pod,
            https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Pod.md
        """

        # convert environment variables to Kubernetes objects
        env_variables = []
        for key, value in image_data.env_variables.items():
            env_variables.append(client.V1EnvVar(name=key, value=value))

        # convert exposed ports to Kubernetes objects
        exposed_ports = []
        if image_data.exposed_ports is not None:
            for port in image_data.exposed_ports:
                splits = port.split("/", 1)
                port = int(splits[0])
                protocol = splits[1].upper() if len(splits) > 1 else None
                exposed_ports.append(client.V1ContainerPort(container_port=port, protocol=protocol))

        # generate container name {image-name}-{username}-{random-4-letters}
        # take just name of image and remove tag
        image_name = image_data.name.split("/")[-1].split(":")[0]
        random_string = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        container_name = '{image_name}-{user_name}-{random_string}'.format(
            image_name=image_name,
            user_name=getpass.getuser(),
            random_string=random_string)

        container = client.V1Container(command=image_data.command,
                                       env=env_variables,
                                       image=image_data.name,
                                       name=container_name,
                                       ports=exposed_ports)

        pod_metadata = client.V1ObjectMeta(name=container_name + "-pod")
        pod_spec = client.V1PodSpec(containers=[container])
        pod = client.V1Pod(spec=pod_spec, metadata=pod_metadata)

        return pod


class PodPhase(enum.Enum):
    """
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
    Additional values in conu:
    TERMINATING - phase right after delete() method is called on pod
    """

    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    FAILED = 3
    TERMINATING = 4
    UNKNOWN = 5

    @classmethod
    def get_from_string(cls, string_phase):
        """
        Convert string value obtained from k8s API to PodPhase enum value
        :param string_phase: str, phase value from Kubernetes API
        :return: PodPhase
        """

        if string_phase == 'Pending':
            return cls.PENDING
        elif string_phase == 'Running':
            return cls.RUNNING
        elif string_phase == 'Succeeded':
            return cls.SUCCEEDED
        elif string_phase == 'Failed':
            return cls.FAILED
        elif string_phase == 'Unknown':
            return cls.UNKNOWN

        return cls.UNKNOWN


class PodCondition(enum.Enum):
    """
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-conditions
    """

    SCHEDULED = 0
    READY = 1
    INITIALIZED = 2
    UNSCHEDULABLE = 3
    CONTAINERS_READY = 4
    UNKNOWN = 5

    @classmethod
    def get_from_string(cls, string_condition):
        """
        Convert string value obtained from k8s API to PodCondition enum value
        :param string_condition: str, condition value from Kubernetes API
        :return: PodCondition
        """

        if string_condition == 'PodScheduled':
            return cls.SCHEDULED
        elif string_condition == 'Ready':
            return cls.READY
        elif string_condition == 'Initialized':
            return cls.INITIALIZED
        elif string_condition == 'Unschedulable':
            return cls.UNSCHEDULABLE
        elif string_condition == 'ContainersReady':
            return cls.CONTAINERS_READY

        return cls.UNKNOWN

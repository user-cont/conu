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

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from conu.utils.probes import Probe
from conu.exceptions import ConuException

config.load_kube_config()
api = client.CoreV1Api()

logger = logging.getLogger(__name__)


class Pod(object):

    def __init__(self, name, namespace, spec):
        """

        :param name: name of pod
        :param namespace: str, namespace in which is pod created
        :param spec: pod spec
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodSpec.md
        """

        self.name = name
        self.namespace = namespace
        self.spec = spec
        self.phase = None

    def delete(self):
        """
        delete pod from the Kubernetes cluster
        :return: None
        """
        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_pod(self.name, self.namespace, body)
            logger.info("Deleting Pod %s in namespace %s" % (self.name, self.namespace))
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
            api_response = api.read_namespaced_pod_status(self.name, self.namespace)
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

    def get_phase(self):
        """
        get phase of the pod
        :return: PodPhase enum

        """

        if self.phase != PodPhase.TERMINATING:
            self.phase = PodPhase.get_from_string(self.get_status().phase)

        return self.phase

    def wait(self, timeout=15):
        """
        block until pod is not running, raises an exc ProbeTimeout if timeout is reached
        :param timeout: int or float (seconds), time to wait for pod to run
        :return: None
        """

        Probe(timeout=timeout, fnc=self.get_phase, expected_retval=PodPhase.RUNNING).run()

    def get_pod_ip(self):
        pass

    def wait(self):
        pass


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
    def get_from_string(cls, string):
        """
        Convert string value obtained from k8s API to PodPhase enum value
        :param string:
        :return: PodPhase
        """
        if string == 'Pending':
            return cls.PENDING
        elif string == 'Running':
            return cls.RUNNING
        elif string == 'Succeeded':
            return cls.SUCCEEDED
        elif string == 'Failed':
            return cls.FAILED
        elif string == 'Unknown':
            return cls.UNKNOWN

        return cls.UNKNOWN

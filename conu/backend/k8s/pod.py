import logging
import enum

from conu.exceptions import ConuException
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from conu.utils.probes import Probe

config.load_kube_config()
api = client.CoreV1Api()

logger = logging.getLogger(__name__)


class Pod(object):

    def __init__(self, name, namespace, spec):
        """

        :param name: name of pod
        :param namespace: str, namespace in which is pod created
        :param spec: pod spec https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodSpec.md
        """

        self.name = name
        self.namespace = namespace
        self.spec = spec

    def delete(self):
        """
        delete pod from the Kubernetes cluster
        :return:
        """
        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_pod(self.name, self.namespace, body)
            if status.status == 'Failure':
                ConuException("Deletion of Pod failed")

        except ApiException as e:
            ConuException("Exception when calling Kubernetes API - delete_namespaced_pod: {}\n".format(e))

    def get_phase(self):
        """
        get status of the pod
        :return: PodPhase enum
        """
        try:
            api_response = api.read_namespaced_pod_status(self.name, self.namespace)
            return PodPhase.get_from_string(api_response.status.phase)
        except ApiException as e:
            ConuException("Exception when calling Kubernetes API - read_namespaced_pod_status: {}\n".format(e))

    def wait(self, timeout=15):
        """
        block until pod is not running, raises an exc ProbeTimeout if timeout is reached
        :param timeout: int or float (seconds), time to wait for pod to run
        :return: None
        """

        Probe(timeout=timeout, fnc=self.get_phase, expected_retval=PodPhase.RUNNING).run()


class PodPhase(enum.Enum):
    """
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
    """

    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    FAILED = 3
    UNKNOWN = 4

    @classmethod
    def get_from_string(cls, string):
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

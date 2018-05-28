from conu.exceptions import ConuException
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import enum

config.load_kube_config()
api = client.CoreV1Api()


class Pod(object):

    def __init__(self, name, namespace, spec):

        self.name = name
        self.namespace = namespace
        self.spec = spec

    def delete(self):
        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_pod(self.name, self.namespace, body)
            if status.status == 'Failure':
                ConuException("Deletion of Pod failed")
        except ApiException as e:
            ConuException("Exception when calling Kubernetes API - delete_namespaced_pod: {}\n".format(e))

    def get_phase(self):
        try:
            api_response = api.read_namespaced_pod_status(self.name, self.namespace)
            return PodPhase.get_from_string(api_response.status.phase)
        except ApiException as e:
            ConuException("Exception when calling Kubernetes API - read_namespaced_pod_status: {}\n".format(e))


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

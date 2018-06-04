from conu.exceptions import ConuException
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from conu.utils.probes import Probe
import logging

from conu.backend.k8s.pod import Pod

config.load_kube_config()
api = client.AppsV1Api()

logger = logging.getLogger(__name__)


class Deployment(object):

    def __init__(self, name, selector, labels, image_metadata, namespace='default'):
        self.name = name
        self.namespace = namespace

        self.pod = Pod.create(image_metadata)

        self.spec = client.V1DeploymentSpec(selector=client.V1LabelSelector(match_labels=selector),
                                            template=client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels=selector),
                                                                              spec=self.pod.spec))

        metadata = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels=labels)

        body = client.V1Deployment(spec=self.spec, metadata=metadata)

        try:
            api.create_namespaced_deployment(self.namespace, body)
        except ApiException as e:
            raise ConuException("Exception when calling Kubernetes API - create_namespaced_deployment: {}\n".format(e))

    def delete(self):
        """
        delete Deployment from the Kubernetes cluster
        :return: None
        """

        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_deployment(self.name, self.namespace, body)

            logger.info("Deleting Service {deployment_name} in namespace: {namespace}".format(deployment_name=self.name,
                                                                                              namespace=self.namespace))
        except ApiException as e:
            raise ConuException("Exception when calling Kubernetes API - delete_namespaced_deployment: {}\n".format(e))

        if status.status == 'Failure':
            raise ConuException("Deletion of Deployment failed")

    def get_status(self):
        """
        get status of the Deployment
        :return: V1DeploymentStatus,
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1DeploymentStatus.md
        """
        try:
            api_response = api.read_namespaced_deployment_status(self.name, self.namespace)
        except ApiException as e:
            raise ConuException(
                "Exception when calling Kubernetes API - read_namespaced_deployment_status: {}\n".format(e))

        print(api_response.status)
        return api_response.status

    def all_pods_ready(self):
        """
        Check if number of replicas with same selector is equals to number of ready replicas
        :return: bool
        """

        print(self.get_status().replicas)
        print(self.get_status().ready_replicas)

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

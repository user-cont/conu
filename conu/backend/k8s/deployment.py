from conu.exceptions import ConuException
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config()
api = client.AppsV1Api()


class Deployment(object):

    def __init__(self, name, namespace, spec=None):
        self.name = name
        self.namespace = namespace
        self.spec = spec or client.V1DeploymentSpec(selector=client.V1LabelSelector(),
                                                    template=client.V1PodTemplateSpec)

        metadata = client.V1ObjectMeta(name=self.name, namespace=self.namespace)

        body = client.V1Deployment(spec=spec, metadata=metadata)

        try:
            api_response = api.create_namespaced_deployment(self.namespace, body)
            print('Deployment created')
        except ApiException as e:
            print(e)
            ConuException("Exception when calling Kubernetes API - create_namespaced_deployment: {}\n".format(e))

    def delete(self):
        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_deployment(self.name, self.namespace, body)
            if status.status == 'Failure':
                ConuException("Deletion of Deployment failed")
        except ApiException as e:
            ConuException("Exception when calling Kubernetes API - delete_namespaced_deployment: {}\n".format(e))

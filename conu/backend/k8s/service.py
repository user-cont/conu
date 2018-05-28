from conu.exceptions import ConuException
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config()
api = client.CoreV1Api()


class Service(object):

    def __init__(self, name, namespace, spec=None):
        self.name = name
        self.namespace = namespace
        self.spec = spec or client.V1ServiceSpec()

        metadata = client.V1ObjectMeta(name=self.name, namespace=self.namespace)

        body = client.V1Service(spec=spec, metadata=metadata)

        try:
            api_response = api.create_namespaced_service(self.namespace, body)
            print('Service created')
        except ApiException as e:
            print(e)
            ConuException("Exception when calling Kubernetes API - create_namespaced_service: {}\n".format(e))

    def delete(self):
        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_service(self.name, self.namespace, body)
            if status.status == 'Failure':
                ConuException("Deletion of Service failed")
        except ApiException as e:
            ConuException("Exception when calling Kubernetes API - delete_namespaced_service: {}\n".format(e))

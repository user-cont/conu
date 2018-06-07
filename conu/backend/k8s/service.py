import logging

from conu.exceptions import ConuException
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from conu.utils.http_client import HttpClient, get_url

from contextlib import contextmanager

import requests

config.load_kube_config()
api = client.CoreV1Api()

logger = logging.getLogger(__name__)


class Service(object):

    def __init__(self, name, ports, namespace='default', labels=None, selector=None):
        """
        :param name: str, name of the service
        :param namespace: str, name of the namespace
        :param ports: list of str, list of exposed ports, example:
                - ['1234/tcp', '8080/udp']
        :param labels: dict, dict of labels
        :param selector: dict, route service traffic to pods with label keys and values matching this selector
        """
        self.name = name
        self.namespace = namespace
        self.ports = ports

        exposed_ports = []

        # create Kubernetes service port objects
        for port in self.ports:
            splits = port.split("/", 1)
            port = int(splits[0])
            protocol = splits[1].upper() if len(splits) > 1 else None
            exposed_ports.append(client.V1ServicePort(port=port, protocol=protocol))

        metadata = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels=labels)
        self.spec = client.V1ServiceSpec(ports=exposed_ports, selector=selector)

        body = client.V1Service(spec=self.spec, metadata=metadata)

        # provides HTTP client (requests.Session)
        self.http_session = requests.Session()

        try:
            api.create_namespaced_service(self.namespace, body)
        except ApiException as e:
            print(e)
            raise ConuException("Exception when calling Kubernetes API - create_namespaced_service: {}\n".format(e))

    def delete(self):
        """
        delete service from the Kubernetes cluster
        :return: None
        """

        body = client.V1DeleteOptions()

        try:
            status = api.delete_namespaced_service(self.name, self.namespace, body)

            logger.info("Deleting Service {service_name} in namespace:{namespace}".format(service_name=self.name,
                                                                                          namespace=self.namespace))
        except ApiException as e:
            raise ConuException("Exception when calling Kubernetes API - delete_namespaced_service: {}\n".format(e))

        if status.status == 'Failure':
            raise ConuException("Deletion of Service failed")

    def get_status(self):
        """
        get status of service
        :return: V1ServiceStatus, https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ServiceStatus.md
        """

        try:
            api_response = api.read_namespaced_service_status(self.name, self.namespace)
        except ApiException as e:
            raise ConuException("Exception when calling Kubernetes API - read_namespaced_service_status: {}\n".format(e))

        return api_response.status

    def get_ip(self):
        """
        get IP adress of service
        :return: str, IP address
        """

        return self.spec.cluster_ip

    @contextmanager
    def http_client(self, host=None, port=None):
        """
        allow requests in context -- e.g.:

        .. code-block:: python

            with container.http_client(port="80", ...) as c:
                assert c.get("/api/...")


        :param host: str, if None, set self.get_IPv4s()[0]
        :param port: str or int, if None, set to self.get_ports()[0]
        :return: instance of :class:`conu.utils.http_client.HttpClient`
        """

        host = host or self.get_ip()
        port = port or self.ports[0]

        yield HttpClient(host, port, self.http_session)

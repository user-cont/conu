from conu.backend.k8s.backend import K8sBackend
from conu.backend.docker.backend import DockerBackend
from conu.backend.k8s.pod import PodPhase

import logging

# insert your API key
API_KEY = "M0XufKHjTsl87t1A4y7Vp0qAYSiKq8n7QauYI3sAHcU"
with K8sBackend(api_key=API_KEY, logging_level=logging.DEBUG) as k8s_backend:

    namespace = k8s_backend.create_namespace()

    with DockerBackend(logging_level=logging.DEBUG) as backend:
        image = backend.ImageClass('nginx')

        pod = image.run_in_pod(namespace=namespace)

        try:
            pod.get_logs()
            pod.wait(200)
            assert pod.is_ready()
        finally:
            pod.get_logs()
            pod.delete()
            assert pod.get_phase() == PodPhase.TERMINATING
            k8s_backend.delete_namespace(namespace)

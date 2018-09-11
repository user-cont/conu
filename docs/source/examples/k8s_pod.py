import logging 

from conu.backend.k8s.backend import K8sBackend
from conu.backend.docker.backend import DockerBackend
from conu.backend.k8s.pod import PodPhase
from conu.utils import run_cmd

api_key = run_cmd(["oc", "whoami", "-t"], return_output=True).rstrip()
with K8sBackend(api_key=api_key, logging_level=logging.DEBUG) as k8s_backend:

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

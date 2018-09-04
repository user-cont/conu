from conu.backend.k8s.backend import K8sBackend
from conu.backend.docker.backend import DockerBackend
from conu.backend.k8s.pod import PodPhase


with K8sBackend() as k8s_backend:

    namespace = k8s_backend.create_namespace()

    with DockerBackend() as backend:
        image = backend.ImageClass('nginx')

        pod = image.run_in_pod(namespace=namespace)

        try:
            pod.wait(200)
            assert pod.is_ready()
        finally:
            pod.get_logs()
            pod.delete()
            assert pod.get_phase() == PodPhase.TERMINATING
            k8s_backend.delete_namespace(namespace)

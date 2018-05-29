from conu import DockerBackend
from conu.backend.k8s.pod import PodPhase
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG


def test_pod():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

        pod = image.run_in_pod()

        pod.wait()

        try:
            assert pod.get_phase() == PodPhase.RUNNING
        finally:
            pod.delete()

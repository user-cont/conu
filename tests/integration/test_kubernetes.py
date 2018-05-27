import pytest
from conu import DockerBackend
from conu.backend.kubernetes.pod import PodPhase
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
    FEDORA_REPOSITORY


def test_pod():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

        pod = image.run_in_pod()

        try:
            assert pod.get_phase() == PodPhase.RUNNING or pod.get_phase() == PodPhase.SUCCEEDED or pod.get_phase() == PodPhase.PENDING
        finally:
            pod.delete()

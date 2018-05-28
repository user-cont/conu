import pytest
from conu import DockerBackend
from conu.backend.k8s.pod import PodPhase
from conu.backend.k8s.deployment import Deployment
from conu.backend.k8s.service import Service
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
    FEDORA_REPOSITORY


def test_pod():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

        pod = image.run_in_pod()

        try:
            assert (pod.get_phase() == PodPhase.RUNNING or
                    pod.get_phase() == PodPhase.SUCCEEDED or
                    pod.get_phase() == PodPhase.PENDING)
        finally:
            pod.delete()


def test_service():

    service = Service('new-service', 'default')
    service.delete()


def test_deployment():

    deployment = Deployment('new-deployment', 'default')
    deployment.delete()

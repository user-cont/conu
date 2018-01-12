import logging

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG

from conu import DockerImage, DockerRunBuilder, DockerBackend
from conu.backend.docker.client import get_client


def test_cleanup_containers():
    backend = DockerBackend(logging_level=logging.DEBUG)

    # cleaning up from previous runs
    backend.cleanup_containers()

    client = get_client()
    container_sum = len(client.containers(all=True))
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    command = DockerRunBuilder(command=["ls"], additional_opts=["-i", "-t"])

    for i in range(3):
        image.run_via_binary(command)

    assert container_sum+3 == len(client.containers(all=True))
    backend.cleanup_containers()
    assert container_sum == len(client.containers(all=True))

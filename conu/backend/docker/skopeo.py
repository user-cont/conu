"""
Wrapping skopeo's functionality
"""

from enum import Enum
from conu.exceptions import ConuException


class Transport(Enum):
    """
    This enum defines transports for skopeo.
    ...
    """
    CONTAINERS_STORAGE = 0
    DIRECTORY = 1
    DOCKER = 2
    DOCKER_ARCHIVE = 3
    DOCKER_DAEMON = 4
    OCI = 5
    OSTREE = 6


def transport_param(image):
    """ WIP: Parse DockerImage info into skopeo parameter

    :param image: DockerImage
    :return: string. skopeo parameter specifying image
    """
    transports = {Transport.CONTAINERS_STORAGE: "containers-storage:",
                  Transport.DIRECTORY: "dir:",
                  Transport.DOCKER: "docker://",
                  Transport.DOCKER_ARCHIVE: "docker-archive",
                  Transport.DOCKER_DAEMON: "docker-daemon:",
                  Transport.OCI: "oci:",
                  Transport.OSTREE: "ostree:"}

    transport = image.transport
    tag = image.tag
    repository = image.name
    path = image.path

    if not transport:
        transport = Transport.DOCKER
    command = transports[transport]

    path_required = [Transport.DIRECTORY, Transport.DOCKER_ARCHIVE, Transport.OCI]
    if transport in path_required and path is None:
        raise ValueError(transports[transport] + " path is required to be specified")

    if transport == Transport.DIRECTORY:
        return command + path
    if transport == Transport.DOCKER_ARCHIVE:
        command += path
        if repository is None:
            return command
        command += ":"
    if transport in [Transport.CONTAINERS_STORAGE, Transport.DOCKER,
                     Transport.DOCKER_ARCHIVE, transport.DOCKER_DAEMON]:
        return command + repository + ":" + tag
    if transport == Transport.OCI:
        return command + path + ":" + tag
    if transport == Transport.OSTREE:
        return command + repository + ("@" + path if path else "")

    raise ConuException("This transport is not supported")

"""
Wrapping skopeo's functionality
"""

from enum import Enum
from conu.exceptions import ConuException


class SkopeoTransport(Enum):
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
    """ Parse DockerImage info into skopeo parameter

    :param image: DockerImage
    :return: string. skopeo parameter specifying image
    """
    transports = {SkopeoTransport.CONTAINERS_STORAGE: "containers-storage:",
                  SkopeoTransport.DIRECTORY: "dir:",
                  SkopeoTransport.DOCKER: "docker://",
                  SkopeoTransport.DOCKER_ARCHIVE: "docker-archive",
                  SkopeoTransport.DOCKER_DAEMON: "docker-daemon:",
                  SkopeoTransport.OCI: "oci:",
                  SkopeoTransport.OSTREE: "ostree:"}

    transport = image.transport
    tag = image.tag
    repository = image.name
    path = image.path

    if not transport:
        transport = SkopeoTransport.DOCKER
    command = transports[transport]

    path_required = [SkopeoTransport.DIRECTORY, SkopeoTransport.DOCKER_ARCHIVE, SkopeoTransport.OCI]
    if transport in path_required and path is None:
        raise ValueError(transports[transport] + " path is required to be specified")

    if transport == SkopeoTransport.DIRECTORY:
        return command + path
    if transport == SkopeoTransport.DOCKER_ARCHIVE:
        command += path
        if repository is None:
            return command
        command += ":"
    if transport in [SkopeoTransport.CONTAINERS_STORAGE, SkopeoTransport.DOCKER,
                     SkopeoTransport.DOCKER_ARCHIVE, transport.DOCKER_DAEMON]:
        return command + repository + ":" + tag
    if transport == SkopeoTransport.OCI:
        return command + path + ":" + tag
    if transport == SkopeoTransport.OSTREE:
        return command + repository + ("@" + path if path else "")

    raise ConuException("This transport is not supported")

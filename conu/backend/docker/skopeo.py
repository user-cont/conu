import enum


class Transport(enum.Enum):
    CONTAINERS_STORAGE = 0
    DIRECTORY = 1
    DOCKER = 2
    DOCKER_ARCHIVE = 3
    DOCKER_DAEMON = 4
    OCI = 5
    OSTREE = 6


def transport_param(transport, repository, tag, path=None):
    """
    Parses info into skopeo parameter
    :param transport: Transport value
    :param repository: docker repository
    :param tag: docker repo tag
    :param path: required for dir and docker-archive transports
    :return: string. skopeo parameter specifying image
    """
    transports = {Transport.CONTAINERS_STORAGE:"containers-storage:",
                  Transport.DIRECTORY: "dir:",
                  Transport.DOCKER: "docker://",
                  Transport.DOCKER_ARCHIVE: "docker-archive",
                  Transport.DOCKER_DAEMON: "docker-daemon:",
                  Transport.OCI: "oci:",
                  Transport.OSTREE: "ostree:"}

    command = transports[transport]
    path_needing = [Transport.DIRECTORY, Transport.DOCKER_ARCHIVE, Transport.OCI]
    if transport in path_needing and path is None:
        raise ValueError(transports[transport] + " path is required to be specified")

    if transport == Transport.DIRECTORY:
        return command + path
    if transport == Transport.DOCKER_ARCHIVE:
        command += path
        if repository is None:
            return command
        command += ":"
    if transport in [Transport.CONTAINERS_STORAGE, Transport.DOCKER, Transport.DOCKER_ARCHIVE, transport.DOCKER_DAEMON]:
        return command + repository + ":" + tag
    if transport == Transport.OCI:
        return command + path + ":" + tag

    raise NotImplementedError(transports[transport] + "transport is not implemented yet")

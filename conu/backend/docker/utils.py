"""
utility functions for related to docker
"""
import logging

from conu.apidefs.metadata import ContainerStatus
from conu.utils import graceful_get


logger = logging.getLogger(__name__)


def inspect_to_metadata(metadata_object, inspect_data):
    """
    process data from `docker inspect` and update provided metadata object

    :param metadata_object: instance of Metadata
    :param inspect_data: dict, metadata from `docker inspect` or `dockert_client.images()`
    :return: instance of Metadata
    """
    identifier = graceful_get(inspect_data, 'Id')
    if identifier:
        if ":" in identifier:
            # format of image name from docker inspect:
            # sha256:8f0e66c924c0c169352de487a3c2463d82da24e9442fc097dddaa5f800df7129
            metadata_object.identifier = identifier.split(':')[1]
        else:
            # container
            metadata_object.identifier = identifier

    # format of Environment Variables from docker inspect:
    # ['DISTTAG=f26container', 'FGC=f26']
    raw_env_vars = graceful_get(inspect_data, "Config", "Env") or []
    if raw_env_vars:
        metadata_object.env_variables = {}
        for env_variable in raw_env_vars:
            splits = env_variable.split("=", 1)
            name = splits[0]
            value = splits[1] if len(splits) > 1 else None
            if value is not None:
                metadata_object.env_variables.update({name: value})

    raw_exposed_ports = graceful_get(inspect_data, "Config", "ExposedPorts")
    if raw_exposed_ports:
        metadata_object.exposed_ports = list(raw_exposed_ports.keys())

    # specific to images
    raw_repo_tags = graceful_get(inspect_data, 'RepoTags')
    if raw_repo_tags:
        metadata_object.name = raw_repo_tags[0]
    metadata_object.labels = graceful_get(inspect_data, 'Config', 'Labels')
    metadata_object.command = graceful_get(inspect_data, 'Config', 'Cmd')
    metadata_object.creation_timestamp = inspect_data.get('Created', None)
    # specific to images
    metadata_object.image_names = inspect_data.get('RepoTags', None)
    # specific to images
    digests = inspect_data.get("RepoDigests", None)
    if digests:
        metadata_object.repo_digests = digests
        metadata_object.digest = digests[0]

    return metadata_object


def inspect_to_container_metadata(c_metadata_object, inspect_data, image_instance):
    """
    process data from `docker container inspect` and update provided container metadata object

    :param c_metadata_object: instance of ContainerMetadata
    :param inspect_data: dict, metadata from `docker inspect` or `dockert_client.images()`
    :param image_instance: instance of DockerImage
    :return: instance of ContainerMetadata
    """
    inspect_to_metadata(c_metadata_object, inspect_data)

    status = ContainerStatus.get_from_docker(
        graceful_get(inspect_data, "State", "Status"),
        graceful_get(inspect_data, "State", "ExitCode"),
    )

    image_id = graceful_get(inspect_data, "Image")
    if image_id:
        if ":" in image_id:
            # format of image name from docker inspect:
            # sha256:8f0e66c924c0c169352de487a3c2463d82da24e9442fc097dddaa5f800df7129
            image_instance.identifier = image_id.split(':')[1]
        else:
            # container
            image_instance.identifier = image_id

    # format of Port mappings from docker inspect:
    # {'12345/tcp': [
    #   {'HostIp': '0.0.0.0', 'HostPort': '123'},
    #   {'HostIp': '0.0.0.0', 'HostPort': '1234'}]}
    port_mappings = dict()

    raw_port_mappings = graceful_get(inspect_data, 'HostConfig', 'PortBindings') or {}

    for key, value in raw_port_mappings.items():
        for item in value:
            logger.debug("parsing ports: key = %s, item = %s", key, item)
            li = port_mappings.get(key, [])
            raw_host_port = item['HostPort']
            if raw_host_port == "":
                int_port = None
            else:
                try:
                    int_port = int(raw_host_port)
                except ValueError as ex:
                    logger.error("could not parse port: %s", ex)
                    continue
            li.append(int_port)
            port_mappings.update({key: li})

    c_metadata_object.status = status
    c_metadata_object.port_mappings = port_mappings
    c_metadata_object.hostname = graceful_get(inspect_data, 'Config', 'Hostname')
    raw_networks = graceful_get(inspect_data, "NetworkSettings", "Networks").values()
    if raw_networks:
        c_metadata_object.ipv4_addresses = [
            graceful_get(x, "IPAddress")
            for x in raw_networks if graceful_get(x, "IPAddress")]
        c_metadata_object.ipv6_addresses = [
            graceful_get(x, "GlobalIPv6Address")
            for x in raw_networks if graceful_get(x, "GlobalIPv6Address")]
    c_metadata_object.image = image_instance
    name = graceful_get(inspect_data, "Name")
    if name:
        name = name[1:] if name.startswith("/") else name  # remove / at the beginning
        c_metadata_object.name = name

    return c_metadata_object

import enum


class Metadata(object):
    """
    Common metadata for container and image
    """

    def __init__(self, name=None, identifier=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None):
        """
        :param name: str, name of object
        :param identifier: int, id of object
        :param labels: dict, {key: value}
        :param command: str, command to be executed
        :param creation_timestamp: str, creation time of object instance
        :param env_variables: dict, {name: value}
        """

        self.name = name
        self.identifier = identifier
        self.labels = labels
        self.command = command
        self.creation_timestamp = creation_timestamp
        self.env_variables = env_variables


class ContainerMetadata(Metadata):
    """
    Specific metadata for container
    """

    def __init__(self, name=None, identifier=None, ports=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None,
                 image=None, hostname=None, ipv4_addresses=None, ipv6_addresses=None, status=None):
        """
        :param name: str, name of container
        :param identifier: int, id of container
        :param ports: list, list of ports
        :param labels: dict, {key: value}
        :param command: str, command to be executed
        :param creation_timestamp: str, creation time of container
        :param env_variables: dict, {name: value}
        :param image: str, name of the image
        :param hostname: str, hostname
        :param ipv4_addresses: dict, {address: port}
        :param ipv6_addresses: dict, {address: port}
        :param status: ContainerStatus, container status value, example:
            - [ContainerStatus.RUNNING]
            - [ContainerStatus.EXITED]
        """

        super(ContainerMetadata, self).__init__(
            name=name, identifier=identifier, labels=labels, command=command,
            creation_timestamp=creation_timestamp, env_variables=env_variables)
        self.ports = ports
        self.hostname = hostname
        self.image = image
        self.ipv4_addresses = ipv4_addresses
        self.ipv6_addresses = ipv6_addresses
        self.status = status


class ImageMetadata(Metadata):
    """
    Specific metadata for image
    """

    def __init__(self, name=None, identifier=None, ports=None, labels=None, command=None, creation_timestamp=None,
                 env_variables=None, image_names=None):
        """
        :param name: str, name of image
        :param identifier: int, id of image
        :param ports: list, list of ports
        :param labels: dict, {key: value} example:
            - {"io.k8s.display-name": "nginx"}
        :param command: str, command to be executed
        :param creation_timestamp: str, creation time of image
        :param env_variables: dict, {name: value}, example:
            - {"MYSQL_PASSWORD": "password"}
        :param image_names: str, image name, example:
            - fedora
            - docker.io/library/fedora:latest
        """

        super(ImageMetadata, self).__init__(
            name=name, identifier=identifier, labels=labels, command=command,
            creation_timestamp=creation_timestamp, env_variables=env_variables)
        self.ports = ports
        self.image_names = image_names


class ContainerStatus(enum.Enum):
    """
    This Enum defines the status of container
    """

    CREATED = 0
    RESTARTING = 1
    RUNNING = 2
    REMOVING = 3
    PAUSED = 4
    EXITED = 5
    DEAD = 6

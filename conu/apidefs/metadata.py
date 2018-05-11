import enum


class Metadata(object):
    """
    Common metadata for container and image
    """

    def __init__(self, name=None, identifier=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None):
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
                 image=None, hostname=None, ipv4=None, ipv6=None, status=None):
        super(ContainerMetadata, self).__init__(
            name=name, identifier=identifier, labels=labels, command=command,
            creation_timestamp=creation_timestamp, env_variables=env_variables)
        self.ports = ports
        self.hostname = hostname
        self.image = image
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.status = status


class ImageMetadata(Metadata):
    """
    Specific metadata for image
    """

    def __init__(self, name=None, identifier=None, ports=None, labels=None, command=None, creation_timestamp=None,
                 env_variables=None, image_names=None):
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

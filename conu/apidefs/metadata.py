class Metadata:
    """
    Common metadata for container and image
    """

    def __init__(self, name=None, id=None, ports=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None):
        self.name = name
        self.id = id
        self.ports = ports
        self.labels = labels
        self.command = command
        self.creation_timestamp = creation_timestamp
        self.env_variables = env_variables


class ContainerMetadata(Metadata):
    """
    Specific metadata for container
    """

    def __init__(self, name=None, id=None, ports=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None,
                 image=None, hostname=None, ipv4=None, ipv6=None, status=None):
        super(ContainerMetadata, self).__init__(
            name=name, id=id, ports=ports, labels=labels, command=command,
            creation_timestamp=creation_timestamp, env_variables=env_variables)
        self.hostname = hostname
        self.image = image
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.status = status


class ImageMetadata(Metadata):
    """
    Specific metadata for image
    """

    def __init__(self, name=None, id=None, ports=None, labels=None, command=None, creation_timestamp=None,
                 env_variables=None, tags=None, registry=None, entrypoint=None):
        super(ImageMetadata, self).__init__(
            name=name, id=id, ports=ports, labels=labels, command=command,
            creation_timestamp=creation_timestamp, env_variables=env_variables)

        self.tags = tags
        self.registry = registry
        self.entrypoint = entrypoint

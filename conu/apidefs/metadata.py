import enum


class Metadata(object):
    """
    Common metadata for container and image
    """

    def __init__(self, name=None, identifier=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None):
        """
        :param name: str, name of object
        :param identifier: str, id of object
        :param labels: dict, {key: value}
        :param command: list of str, command to run in the container, example:
            - ["psql", "--version"]
            - ["python3", "-m", "http.server", "--bind", "0.0.0.0", "8080"]
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

    def __init__(self, name=None, identifier=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None,
                 image=None, exposed_ports=None, port_mappings=None, hostname=None,
                 ipv4_addresses=None, ipv6_addresses=None, status=None):
        """
        :param name: str, name of container
        :param identifier: str, id of container
        :param labels: dict, {key: value}
        :param command: list of str, command to run in the container, example:
            - ["psql", "--version"]
            - ["python3", "-m", "http.server", "--bind", "0.0.0.0", "8080"]
        :param creation_timestamp: str, creation time of container
        :param env_variables: dict, {name: value}
        :param image: Image, reference to Image instance
        :param exposed_ports: list, list of exposed ports
        :param port_mappings: dict, dictionary of port mappings {"container_port": [host_port1]}, example:
            - {"1111/tcp":[1234, 4567]} bind host ports 1234 and 4567 to a single container port 1111/tcp
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
        self.exposed_ports = exposed_ports
        self.port_mappings = port_mappings
        self.hostname = hostname
        self.image = image
        self.ipv4_addresses = ipv4_addresses
        self.ipv6_addresses = ipv6_addresses
        self.status = status


class ImageMetadata(Metadata):
    """
    Specific metadata for image
    """

    def __init__(self, name=None, identifier=None, labels=None, command=None,
                 creation_timestamp=None, env_variables=None, exposed_ports=None, image_names=None):
        """
        :param name: str, name of image
        :param identifier: str, id of image
        :param labels: dict, {key: value} example:
            - {"io.k8s.display-name": "nginx"}
        :param command: list of str, command to run in the container, example:
            - ["psql", "--version"]
            - ["python3", "-m", "http.server", "--bind", "0.0.0.0", "8080"]
        :param creation_timestamp: str, creation time of image
        :param env_variables: dict, {name: value}, example:
            - {"MYSQL_PASSWORD": "password"}
        :param exposed_ports: list, list of exposed ports
        :param image_names: str, image name, example:
            - fedora
            - docker.io/library/fedora:latest
        """

        super(ImageMetadata, self).__init__(
            name=name, identifier=identifier, labels=labels, command=command,
            creation_timestamp=creation_timestamp, env_variables=env_variables)
        self.exposed_ports = exposed_ports
        self.image_names = image_names


class ContainerStatus(enum.Enum):
    """
    This Enum defines the status of container
    """

    RUNNING = 0
    NOT_RUNNING = 1
    UNKNOWN = 2
    FAILED = 3

    @classmethod
    def get_from_docker(cls, string, exit_code):
        if exit_code != 0:
            return ContainerStatus.FAILED
        elif string == 'created':
            return ContainerStatus.NOT_RUNNING
        elif string == 'restarting':
            return ContainerStatus.UNKNOWN
        elif string == 'running':
            return ContainerStatus.RUNNING
        elif string == 'removing':
            return ContainerStatus.UNKNOWN
        elif string == 'paused':
            return ContainerStatus.NOT_RUNNING
        elif string == 'exited':
            return ContainerStatus.NOT_RUNNING
        elif string == 'dead':
            return ContainerStatus.FAILED
        else:
            return ContainerStatus.UNKNOWN

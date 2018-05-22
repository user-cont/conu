from conu.apidefs.metadata import ContainerMetadata


class DockerContainerParameters(ContainerMetadata):

    def __init__(self, cap_add=None, cap_drop=None, command=None, detach=False,
                 devices=None, dns=None, entrypoint=None, env_variables=None, group_add=None,
                 healthcheck=None, hostname=None, init=False, ipc_mode=None, isolation=None,
                 labels=None, mac_address=None, mem_limit=None, mounts=None,
                 name=None, network=None, pids_limit=None, platform=None,
                 port_mappings=None, privileged=False, publish_all_ports=False, read_only=False,
                 remove=False, runtime=None, stdin_open=False, stdout=True,
                 stderr=False, stop_signal=None, tty=False, user=None, volumes=None, working_dir=None):
        """
        See docker-py documentation: https://docker-py.readthedocs.io/en/stable/containers.html
        """

        super(DockerContainerParameters, self).__init__(name=name, labels=labels, command=command,
                                                        env_variables=env_variables, port_mappings=port_mappings,
                                                        hostname=hostname)

        self.cap_add = cap_add
        self.cap_drop = cap_drop
        self.detach = detach
        self.devices = devices
        self.dns = dns
        self.entrypoint = entrypoint
        self.group_add = group_add
        self.healthcheck = healthcheck
        self.init = init
        self.ipc_mode = ipc_mode
        self.isolation = isolation
        self.mac_address = mac_address
        self.mem_limit = mem_limit
        self.mounts = mounts
        self.network = network
        self.pids_limit = pids_limit
        self.platform = platform
        self.privileged = privileged
        self.publish_all_ports = publish_all_ports
        self.read_only = read_only
        self.remove = remove
        self.runtime = runtime
        self.stdin_open = stdin_open
        self.stdout = stdout
        self.stderr = stderr
        self.stop_signal = stop_signal
        self.tty = tty
        self.user = user
        self.volumes = volumes
        self.working_dir = working_dir

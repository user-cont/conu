"""
singleton instance of docker.Client
"""
from __future__ import print_function, unicode_literals

from conu.utils import check_docker_command_works

import podman

client = None


def get_client():
    global client
    if client is None:
        check_docker_command_works()
        try:
            client = podman.Client()
        except AttributeError:
            raise AttributeError
    return client

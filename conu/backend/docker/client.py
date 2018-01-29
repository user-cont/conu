"""
singleton instance of docker.APIClient
"""
from __future__ import print_function, unicode_literals

from conu.utils import check_docker_command_works

import docker


client = None


def get_client():
    global client
    if client is None:
        client = docker.APIClient(version="auto")
        # FIXME: once we implement `run_via_api`, move this elsewhere; ideally to run_via_binary
        #        and check only once
        check_docker_command_works()
    return client

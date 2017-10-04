"""
singleton instance of docker.APIClient
"""
from __future__ import print_function, unicode_literals

import docker

client = None


def get_client():
    global client
    if client is None:
        client = docker.APIClient(version="auto")
    return client

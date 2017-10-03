"""
singleton instance of docker.APIClient
"""

import docker

client = None


def get_client():
    global client
    if client is None:
        client = docker.APIClient(version="auto")
    return client

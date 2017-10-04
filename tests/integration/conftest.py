"""
Prepare testing environment for integration testing

This file has to be named conftest.py!
"""
from __future__ import print_function, unicode_literals

import subprocess

# fails when doing absolute import
from .constants import FEDORA_MINIMAL_IMAGE, THE_HELPER_IMAGE, FEDORA_REPOSITORY

import pytest


def obtain_images():
    subprocess.check_call(["docker", "image", "pull", FEDORA_MINIMAL_IMAGE])
    subprocess.check_call(["docker", "image", "pull", FEDORA_REPOSITORY])
    subprocess.check_call(["docker", "container", "run", "--name", "nc-container",
                           FEDORA_MINIMAL_IMAGE, "microdnf", "install", "nmap-ncat"])
    subprocess.check_call(["docker", "container", "commit", "nc-container", THE_HELPER_IMAGE])
    subprocess.check_call(["docker", "container", "rm", "nc-container"])


@pytest.fixture(autouse=True, scope='session')
def setup_test_session():
    for x in [FEDORA_MINIMAL_IMAGE, THE_HELPER_IMAGE, FEDORA_REPOSITORY]:
        try:
            subprocess.check_call(["docker", "image", "inspect", x], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            break
    # executed if not break raised
    else:
        # all images were found, we're good
        return
    # the loop ended with break, create images
    obtain_images()

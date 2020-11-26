# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#
"""
Prepare testing environment for integration testing

This file has to be named conftest.py!
"""
from __future__ import print_function, unicode_literals

import os
import logging
import subprocess

# fails when doing absolute import
from tests.constants import FEDORA_MINIMAL_REPOSITORY_DIGEST
from ..constants import FEDORA_MINIMAL_IMAGE, THE_HELPER_IMAGE, FEDORA_REPOSITORY, S2I_IMAGE

import pytest


log = logging.getLogger("conu.tests")


def obtain_images():
    for image in (FEDORA_MINIMAL_IMAGE, FEDORA_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_DIGEST):
        for tool in ("podman", "docker"):
            subprocess.check_call([tool, "image", "pull", image])
    for tool in ("podman", "docker"):
        subprocess.check_call([tool, "container", "run", "--name", "nc-container",
                               FEDORA_MINIMAL_IMAGE, "microdnf", "install", "nmap-ncat"])
        subprocess.check_call([tool, "container", "commit", "nc-container", THE_HELPER_IMAGE])
        subprocess.check_call([tool, "container", "rm", "nc-container"])
    build_punchbag()  # pull base images first


def build_punchbag():
    """ punchbag is our s2i image """
    log.info("building test s2i image - punchbag")
    integration_tests_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(integration_tests_dir, "data")
    image_dir = os.path.join(data_dir, "punchbag")
    for tool in ("podman", "docker"):
        c = [tool, "image", "build", "--tag", "punchbag", image_dir]
        log.debug("command = %s", c)
        subprocess.check_call(c)


@pytest.fixture(autouse=True, scope='session')
def setup_test_session():
    for x in [FEDORA_MINIMAL_IMAGE, THE_HELPER_IMAGE, FEDORA_REPOSITORY, S2I_IMAGE,
              FEDORA_MINIMAL_REPOSITORY_DIGEST]:
        try:
            subprocess.check_call(["docker", "image", "inspect", x], stdout=subprocess.PIPE)
            subprocess.check_call(["podman", "image", "inspect", x], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            break
    # executed if break was not reached
    else:
        # all images were found, we're good
        return
    # the loop ended with break, create images
    obtain_images()

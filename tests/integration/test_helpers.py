# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

from conu.fixtures import docker_backend
from conu.helpers import get_container_output
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG


def test_get_container_output(docker_backend):
    output = get_container_output(docker_backend, FEDORA_MINIMAL_REPOSITORY,
                                  ["cat", "/etc/os-release"],
                                  image_tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    assert FEDORA_MINIMAL_REPOSITORY_TAG in output

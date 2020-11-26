# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

from __future__ import print_function, unicode_literals

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG
from conu import DockerRunBuilder, DockerImage
from conu.backend.docker.constants import CONU_ARTIFACT_TAG


def test_dr_command_class():
    simple = DockerRunBuilder()
    simple.image_name = "voodoo"
    assert ["docker", "run", "-l", CONU_ARTIFACT_TAG, "voodoo"] == simple.build()

    complex = DockerRunBuilder(additional_opts=["-a", "--foo"])
    complex.image_name = "voodoo"
    assert ["docker", "run", "-a", "--foo", "-l", CONU_ARTIFACT_TAG, "voodoo"] == complex.build()

    w_cmd = DockerRunBuilder(command=["x", "y"], additional_opts=["-a", "--foo"])
    w_cmd.image_name = "voodoo"
    assert ["docker", "run", "-a", "--foo", "-l", CONU_ARTIFACT_TAG, "voodoo", "x", "y"] == w_cmd.build()

    # test whether mutable params are not mutable across instances
    simple.options += ["spy"]
    assert "spy" not in DockerRunBuilder().options


def test_get_port_mappings():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

    # the container needs to be running in order to get port mappings
    additional_opts = ["-p", "321:123", "-i"]

    container = image.run_via_binary(additional_opts=additional_opts)
    try:
        mappings = container.get_port_mappings(123)

        assert len(mappings) == 1
        assert mappings == [{"HostIp": '0.0.0.0', "HostPort": '321'}]

        mappings = container.get_port_mappings()
        assert len(mappings) == 1
        assert mappings == {'123/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '321'}]}
    finally:
        container.delete(force=True)

    container = image.run_via_binary()
    try:
        mappings = container.get_port_mappings(123)

        assert not mappings
    finally:
        container.delete(force=True)

# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#


from conu import DockerBackend
from conu.helpers import get_container_output


with DockerBackend() as backend:
    # This will run the container using the supplied command, collects output and
    # cleans the container
    output = get_container_output(backend, "registry.fedoraproject.org/fedora", ["ls", "-1", "/etc"],
                                  image_tag="27")
    assert "passwd" in output

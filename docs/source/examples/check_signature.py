# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

from conu import DockerBackend


def check_signature(backend):
    image = backend.ImageClass('docker.io/modularitycontainers/memcached')
    image.pull()
    image.has_pkgs_signed_with(['812a6b4b64dab85d'])


with DockerBackend() as backend:
    check_signature(backend)

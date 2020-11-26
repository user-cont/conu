# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

from conu import DockerBackend, DockerRunBuilder

with DockerBackend() as backend:
    image = backend.ImageClass('centos/httpd-24-centos7')
    additional_opts = ["-p", "8080:8080"]
    container = image.run_via_binary(additional_opts=additional_opts)
    container.wait_for_port(port=8080, timeout=-1)

    container.stop()
    container.delete()

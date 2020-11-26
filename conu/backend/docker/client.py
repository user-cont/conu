# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

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
        # FIXME: once we implement `run_via_api`, move this elsewhere; ideally to run_via_binary
        #        and check only once
        check_docker_command_works()
        try:
            client = docker.APIClient(version="auto")  # >= 2
        except AttributeError:
            client = docker.Client(version="auto")  # < 2
    return client

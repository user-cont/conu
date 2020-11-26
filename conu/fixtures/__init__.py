# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#
"""
This submodule contains `pytest <https://docs.pytest.org/en/latest/>`_ fixtures
which can be utilized when writing tests for your containers while using conu
and pytest.
"""

import logging

from conu import DockerBackend, PodmanBackend
from conu.backend.buildah.backend import BuildahBackend
from conu.utils import run_cmd

import pytest


@pytest.fixture()
def docker_backend():
    """
    pytest fixture which mimics context manager: it provides new instance of DockerBackend and
    cleans after it once it's used; sample usage:

    ::

        def test_my_container(docker_backend):
            image = docker_backend.ImageClass("fedora", tag="27")

    :return: instance of DockerBackend
    """
    with DockerBackend(logging_level=logging.DEBUG) as backend:
        yield backend
        backend._clean()


@pytest.fixture()
def podman_backend():
    """
        pytest fixture which mimics context manager: it provides new instance of PodmanBackend and
        cleans after it once it's used; behaves the same as docker_backend fixture

        :return: instance of PodmanBackend
        """
    with PodmanBackend(logging_level=logging.DEBUG) as backend:
        yield backend
        backend._clean()


@pytest.fixture()
def buildah_backend():
    """
        pytest fixture which mimics context manager: it provides new instance of BuildahBackend and
        cleans after it once it's used; behaves the same as docker_backend fixture

        :return: instance of BuildahBackend
        """
    with BuildahBackend(logging_level=logging.DEBUG) as backend:
        yield backend
        backend._clean()

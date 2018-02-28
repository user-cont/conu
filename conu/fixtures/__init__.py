# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
This submodule contains `pytest <https://docs.pytest.org/en/latest/>`_ fixtures
which can be utilized when writing tests for your containers while using conu
and pytest.
"""

import logging

from conu import DockerBackend

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
    backend = DockerBackend(logging_level=logging.DEBUG).__enter__()
    yield backend
    backend._clean()

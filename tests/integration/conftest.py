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
Prepare testing environment for integration testing

This file has to be named conftest.py!
"""
from __future__ import print_function, unicode_literals

import os
import logging
import subprocess

# fails when doing absolute import
from ..constants import FEDORA_MINIMAL_IMAGE, THE_HELPER_IMAGE, FEDORA_REPOSITORY, S2I_IMAGE

import pytest


log = logging.getLogger("conu.tests")


def obtain_images():
    subprocess.check_call(["docker", "image", "pull", FEDORA_MINIMAL_IMAGE])
    subprocess.check_call(["docker", "image", "pull", FEDORA_REPOSITORY])
    subprocess.check_call(["docker", "container", "run", "--name", "nc-container",
                           FEDORA_MINIMAL_IMAGE, "microdnf", "install", "nmap-ncat"])
    subprocess.check_call(["docker", "container", "commit", "nc-container", THE_HELPER_IMAGE])
    subprocess.check_call(["docker", "container", "rm", "nc-container"])
    build_punchbag()  # pull base images first


def build_punchbag():
    """ punchbag is our s2i image """
    log.info("building test s2i image - punchbag")
    integration_tests_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(integration_tests_dir, "data")
    image_dir = os.path.join(data_dir, "punchbag")
    c = ["docker", "image", "build", "--tag", "punchbag", image_dir]
    log.debug("command = %s", c)
    subprocess.check_call(c)


@pytest.fixture(autouse=True, scope='session')
def setup_test_session():
    for x in [FEDORA_MINIMAL_IMAGE, THE_HELPER_IMAGE, FEDORA_REPOSITORY, S2I_IMAGE]:
        try:
            subprocess.check_call(["docker", "image", "inspect", x], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            break
    # executed if break was not reached
    else:
        # all images were found, we're good
        return
    # the loop ended with break, create images
    obtain_images()

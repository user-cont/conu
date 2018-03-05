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
These are the tests that verify that our project is released correctly. It only makes sense
to run them after a release.

Just to mess with your brain: this script is using conu to smoke-test conu release in a container.
"""

import logging
import os

import conu
import pytest


BACKEND = conu.DockerBackend(logging_level=logging.DEBUG)


def get_conu_version_from_git():
    version = {}
    # __file__/../../conu/version.py
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    with open(os.path.join(project_dir, "conu", "version.py")) as fp:
        exec(fp.read(), version)
    return version["__version__"]


def run_in_container(img_name, img_tag, script):
    i = BACKEND.ImageClass(img_name, tag=img_tag)
    try:
        i.inspect()
    except Exception:
        i.pull()
    c = i.run_via_binary(command=["sleep", "infinity"], additional_opts=["--rm"])
    try:
        for s in script:
            c.execute(s)
    finally:
        c.stop()


@pytest.mark.parametrize(
    "c", [
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "rawhide",
            "script": [
                ["dnf", "install", "-y", "python3-pip", "python3-pyxattr"],
                ["pip3", "install", "--user", "conu"],
                ["python3", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "rawhide",
            "script": [
                ["dnf", "install", "-y", "python2-pip", "pyxattr"],
                ["pip2", "install", "--user", "conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "27",
            "script": [
                ["dnf", "install", "-y", "python3-pip", "python3-pyxattr"],
                ["pip3", "install", "--user", "conu"],
                ["python3", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "26",
            "script": [
                ["dnf", "install", "-y", "python2-pip", "pyxattr"],
                ["pip2", "install", "--user", "conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "centos",
            "container_image_tag": "7",
            "script": [
                ["yum", "install", "-y", "epel-release"],
                ["yum", "install", "-y", "python-pip"],
                ["pip2", "install", "--user", "conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        }
    ]
)
@pytest.mark.release_pypi
def test_pypi(c):
    # TODO: verify proper exc are being raised when binaries are missing
    run_in_container(
        c["container_image"],
        c["container_image_tag"],
        c["script"],
    )


@pytest.mark.parametrize(
    "c", [
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "rawhide",
            "script": [
                ["dnf", "install", "-y", "dnf-plugins-core"],
                ["dnf", "copr", "enable", "-y", "ttomecek/conu"],
                ["dnf", "install", "-y", "python3-conu"],
                ["python3", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "rawhide",
            "script": [
                ["dnf", "install", "-y", "dnf-plugins-core"],
                ["dnf", "copr", "enable", "-y", "ttomecek/conu"],
                ["dnf", "install", "-y", "python2-conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "27",
            "script": [
                ["dnf", "install", "-y", "dnf-plugins-core"],
                ["dnf", "copr", "enable", "-y", "ttomecek/conu"],
                ["dnf", "install", "-y", "python3-conu"],
                ["python3", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "27",
            "script": [
                ["dnf", "install", "-y", "dnf-plugins-core"],
                ["dnf", "copr", "enable", "-y", "ttomecek/conu"],
                ["dnf", "install", "-y", "python2-conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "26",
            "script": [
                ["dnf", "install", "-y", "dnf-plugins-core"],
                ["dnf", "copr", "enable", "-y", "ttomecek/conu"],
                ["dnf", "install", "-y", "python3-conu"],
                ["python3", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "registry.fedoraproject.org/fedora",
            "container_image_tag": "26",
            "script": [
                ["dnf", "install", "-y", "dnf-plugins-core"],
                ["dnf", "copr", "enable", "-y", "ttomecek/conu"],
                ["dnf", "install", "-y", "python2-conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        },
        {
            "container_image": "centos",
            "container_image_tag": "centos7",
            "script": [
                ["curl", "-s", "-o", "/etc/yum.repos.d/ttomecek-conu.repo",
                 "https://copr.fedorainfracloud.org/coprs/ttomecek/conu/repo/epel-7/ttomecek-conu-epel-7.repo"],
                ["yum", "install", "-y", "python2-conu"],
                ["python2", "-c", "import conu; conu.version == '%s'" % get_conu_version_from_git()],
            ]
        }
    ]
)
@pytest.mark.release_copr
def test_copr(c):
    run_in_container(
        c["container_image"],
        c["container_image_tag"],
        c["script"],
    )

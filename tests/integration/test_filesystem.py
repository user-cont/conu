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
import os

import pytest
import six

from conu.backend.docker.backend import DockerBackend
from conu.backend.docker.container import ConuException

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG


@pytest.fixture()
def docker_image():
    """
    pytest fixture which returns instance of DockerImage
    """
    backend = DockerBackend().__enter__()
    image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    yield image
    backend.__exit__(None, None, None)


@pytest.fixture()
def docker_container():
    """
    pytest fixture which returns instance of DockerImage
    """
    backend = DockerBackend().__enter__()
    image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    container = image.run_via_binary(command=["sleep", "infinity"])
    yield container
    container.delete(force=True)
    backend.__exit__(None, None, None)


def test_container_read_file(docker_container):
    with docker_container.mount() as fs:
        with pytest.raises(ConuException):
            fs.read_file("/i/lost/my/banana")
        content = fs.read_file("/etc/system-release")
    assert content == "Fedora release 26 (Twenty Six)\n"


def test_container_copy_from(docker_container, tmpdir):
    with docker_container.mount() as fs:
        fs.copy_from("/etc/system-release", str(tmpdir))
        with open(os.path.join(str(tmpdir), "system-release")) as fd:
            assert fd.read() == "Fedora release 26 (Twenty Six)\n"

        tmpdir.mkdir("etc")
        if six.PY2:
            with pytest.raises(OSError):
                fs.copy_from("/etc", str(tmpdir))
        else:
            with pytest.raises(FileExistsError):
                fs.copy_from("/etc", str(tmpdir))


def test_container_get_file(docker_container):
    with docker_container.mount() as fs:
        f = fs.get_file("/etc/system-release")
        assert f.fileno()
        assert "/etc/system-release" in f.name
        assert f.read() == "Fedora release 26 (Twenty Six)\n"
        f.close()


def test_container_file_is_present(docker_container):
    with docker_container.mount() as fs:
        assert fs.file_is_present("/etc/system-release")
        assert not fs.file_is_present("/etc/voldemort")
        with pytest.raises(IOError):
            fs.file_is_present("/etc")


def test_container_dir_is_present(docker_container):
    with docker_container.mount() as fs:
        assert fs.directory_is_present("/etc/")
        assert not fs.directory_is_present("/etc/voldemort")
        with pytest.raises(IOError):
            fs.directory_is_present("/etc/passwd")


def test_container_is_unpacked_well(docker_container):
    with docker_container.mount() as fs:
        assert os.path.islink(os.path.join(fs.mount_point, "bin"))
        s = os.stat(os.path.join(fs.mount_point, "usr/bin"))
        assert s.st_uid == os.getuid()
        assert s.st_mode == 0o40555
        assert os.path.isdir(os.path.join(fs.mount_point, "dev"))


def test_image_is_unpacked_well(docker_image):
    with docker_image.mount() as fs:
        assert os.path.islink(os.path.join(fs.mount_point, "bin"))
        s = os.stat(os.path.join(fs.mount_point, "usr/bin"))
        assert s.st_uid == os.getuid()
        assert s.st_mode == 0o40555
        assert os.path.isdir(os.path.join(fs.mount_point, "dev"))


def test_image_read_file(docker_image):
    with docker_image.mount() as fs:
        with pytest.raises(ConuException):
            fs.read_file("/i/lost/my/banana")
        content = fs.read_file("/etc/system-release")
    assert content == "Fedora release 26 (Twenty Six)\n"


def test_image_copy_from(docker_image, tmpdir):
    with docker_image.mount() as fs:
        fs.copy_from("/etc/system-release", str(tmpdir))
        with open(os.path.join(str(tmpdir), "system-release")) as fd:
            assert fd.read() == "Fedora release 26 (Twenty Six)\n"

        tmpdir.mkdir("etc")
        if six.PY2:
            with pytest.raises(OSError):
                fs.copy_from("/etc", str(tmpdir))
        else:
            with pytest.raises(FileExistsError):
                fs.copy_from("/etc", str(tmpdir))


def test_image_get_file(docker_image):
    with docker_image.mount() as fs:
        f = fs.get_file("/etc/system-release")
        assert f.fileno()
        assert "/etc/system-release" in f.name
        assert f.read() == "Fedora release 26 (Twenty Six)\n"
        f.close()


def test_image_file_is_present(docker_image):
    with docker_image.mount() as fs:
        assert fs.file_is_present("/etc/system-release")
        assert not fs.file_is_present("/etc/voldemort")
        with pytest.raises(IOError):
            fs.file_is_present("/etc")


def test_image_dir_is_present(docker_image):
    with docker_image.mount() as fs:
        assert fs.directory_is_present("/etc/")
        assert not fs.directory_is_present("/etc/voldemort")
        with pytest.raises(IOError):
            fs.directory_is_present("/etc/passwd")

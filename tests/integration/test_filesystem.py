import os

import pytest
import six

from conu.backend.docker.backend import DockerBackend
from conu.backend.docker.container import (
    DockerRunBuilder, ConuException
)
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG


@pytest.mark.requires_atomic_cli
class TestDockerContainerFilesystem(object):
    image = None
    container = None

    @classmethod
    def setup_class(cls):
        cls.backend = DockerBackend().__enter__()
        cls.image = cls.backend.ImageClass(
            FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        cls.container = cls.image.run_via_binary(
            DockerRunBuilder(command=["sleep", "infinity"])
        )

    @classmethod
    def teardown_class(cls):
        cls.backend.cleanup_containers()
        cls.backend.__exit__(None, None, None)

    def test_read_file(self):
        with self.container.mount() as fs:
            with pytest.raises(ConuException):
                fs.read_file("/i/lost/my/banana")
            content = fs.read_file("/etc/system-release")
        assert content == "Fedora release 26 (Twenty Six)\n"

    def test_copy_from(self, tmpdir):
        with self.container.mount() as fs:
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

    def test_get_file(self):
        with self.container.mount() as fs:
            f = fs.get_file("/etc/system-release")
            assert f.fileno()
            assert "/etc/system-release" in f.name
            assert f.read() == "Fedora release 26 (Twenty Six)\n"
            f.close()

    def test_file_is_present(self):
        with self.container.mount() as fs:
            assert fs.file_is_present("/etc/system-release")
            assert not fs.file_is_present("/etc/voldemort")
            with pytest.raises(IOError):
                fs.file_is_present("/etc")

    def test_dir_is_present(self):
        with self.container.mount() as fs:
            assert fs.directory_is_present("/etc/")
            assert not fs.directory_is_present("/etc/voldemort")
            with pytest.raises(IOError):
                fs.directory_is_present("/etc/passwd")


@pytest.mark.requires_atomic_cli
class TestDockerImageFilesystem(object):
    image = None

    @classmethod
    def setup_class(cls):
        cls.backend = DockerBackend().__enter__()
        cls.image = cls.backend.ImageClass(
            FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

    @classmethod
    def teardown_class(cls):
        cls.backend.__exit__(None, None, None)

    def test_read_file(self):
        with self.image.mount() as fs:
            with pytest.raises(ConuException):
                fs.read_file("/i/lost/my/banana")
            content = fs.read_file("/etc/system-release")
        assert content == "Fedora release 26 (Twenty Six)\n"

    def test_copy_from(self, tmpdir):
        with self.image.mount() as fs:
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

    def test_get_file(self):
        with self.image.mount() as fs:
            f = fs.get_file("/etc/system-release")
            assert f.fileno()
            assert "/etc/system-release" in f.name
            assert f.read() == "Fedora release 26 (Twenty Six)\n"
            f.close()

    def test_file_is_present(self):
        with self.image.mount() as fs:
            assert fs.file_is_present("/etc/system-release")
            assert not fs.file_is_present("/etc/voldemort")
            with pytest.raises(IOError):
                fs.file_is_present("/etc")

    def test_dir_is_present(self):
        with self.image.mount() as fs:
            assert fs.directory_is_present("/etc/")
            assert not fs.directory_is_present("/etc/voldemort")
            with pytest.raises(IOError):
                fs.directory_is_present("/etc/passwd")

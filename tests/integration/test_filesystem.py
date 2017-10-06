import os

import six

from conu.apidefs.exceptions import ConuException
from .constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG
from conu.backend.docker.container import DockerContainer, DockerRunCommand
from conu.backend.docker.image import DockerImage

from docker.errors import NotFound

import pytest


@pytest.mark.requires_atomic_cli
class TestDockerContainerFilesystem(object):
    containers_to_remove = []
    image = None
    container = None

    @classmethod
    def setup_class(cls):
        cls.image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        cls.container = DockerContainer.run_via_binary(
            cls.image,
            DockerRunCommand(command=["sleep", "infinity"])
        )
        cls.containers_to_remove.append(cls.container.get_id())

    @classmethod
    def teardown_class(cls):
        for c in cls.containers_to_remove:
            try:
                DockerContainer(cls.image, c).rm(force=True, volumes=True)
            except NotFound:  # FIXME: implementation leak, we should own exc for this
                pass

    def test_read_file(self):
        with self.container.mount() as fs:
            with pytest.raises(ConuException):
                fs.read_file("/i/lost/my/banana")
            content = fs.read_file("/etc/system-release")
        assert content == "Fedora release 26 (Twenty Six)\n"

    def test_copy_to(self, tmpdir):
        content = b"gardener did it"
        p = tmpdir.join("secret")
        p.write(content)

        with self.container.mount() as fs:
            fs.copy_to(str(p), "/")
        assert content == self.container.execute(["cat", "/secret"])

    def test_copy_from(self, tmpdir):
        with self.container.mount() as fs:
            fs.copy_from("/etc/system-release", str(tmpdir))
            with open(os.path.join(str(tmpdir), "system-release")) as fd:
                assert fd.read() == "Fedora release 26 (Twenty Six)\n"

            test_file_name = "test-file"
            with open(os.path.join(fs.mount_point, test_file_name), "w") as test_fd:
                test_fd.write("test-content")
            fs.copy_from("/" + test_file_name, str(tmpdir))
            with open(os.path.join(str(tmpdir), test_file_name)) as fd:
                assert fd.read() == "test-content"

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
        cls.image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

    def test_read_file(self):
        with self.image.mount() as fs:
            with raises(ConuException):
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

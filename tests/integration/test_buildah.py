from __future__ import print_function, unicode_literals

import subprocess

import pytest
from six import string_types

from conu import ConuException, random_str
from conu.fixtures import buildah_backend
from conu.backend.buildah.container import BuildahRunBuilder
from conu.backend.buildah.image import BuildahImage, BuildahImagePullPolicy
from conu.utils import check_buildah_command_works
from tests.constants import FEDORA_MINIMAL_IMAGE
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG


def test_buildah_command():
    assert check_buildah_command_works()


def test_buildah_version(buildah_backend):
    assert buildah_backend.get_version() is not None


def test_buildah_image(buildah_backend):
    image = buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    assert "%s:%s" % (FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG) == image.get_full_name()
    insp = image.inspect()
    assert "Config" in insp
    assert isinstance(insp["Config"], str)
    assert "registry.fedoraproject.org/fedora-minimal:26" == str(image)
    assert "BuildahImage(repository=%s, tag=%s)" % (FEDORA_MINIMAL_REPOSITORY,
                                                    FEDORA_MINIMAL_REPOSITORY_TAG) == repr(image)
    assert isinstance(image.get_id(), string_types)
    new_image = image.tag_image(tag="test")
    assert new_image.is_present()
    new_image.rmi(via_name=True)
    assert not new_image.is_present()


def test_image_wrong_types(buildah_backend):
    with pytest.raises(ConuException) as exc:
        buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, BuildahImagePullPolicy.NEVER)
        assert "tag" in exc.value.message


def test_buildah_container(buildah_backend):
    """
    Basic tests of interacting with a buildabuildah
    """
    image = buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    c = image.run_via_binary()
    try:
        assert c.is_running()
        assert "Config" in c.inspect()
        assert c.get_id() == str(c)
        assert repr(c)
        assert isinstance(c.get_id(), string_types)
    finally:
        c.delete(force=True)


def test_container_output(buildah_backend):
    image = buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    command = ["bash", "-c", "for x in `seq 1 5`; do echo $x; done"]
    cont = image.run_via_binary()
    try:
        output = cont.execute(command)
        assert output == '1\n2\n3\n4\n5\n'
    finally:
        cont.delete(force=True)


@pytest.mark.xfail(reason="Bug in buildah: https://github.com/containers/buildah/issues/1813")
def test_exit_code(buildah_backend):
    image = buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = ['bash', '-c', "exit 42"]
    cont = image.run_via_binary()
    try:
        with pytest.raises(subprocess.CalledProcessError) as exc:
            cont.execute(cmd)
        assert exc.value.returncode == 42
    finally:
        cont.delete(force=True)


def test_pull_always(buildah_backend):
    image = buildah_backend.ImageClass("docker.io/library/busybox", tag="latest",
                                       pull_policy=BuildahImagePullPolicy.ALWAYS)
    try:
        assert image.is_present()
    finally:
        image.rmi(force=True)


def test_pull_if_not_present(buildah_backend):
    image = buildah_backend.ImageClass("docker.io/library/busybox", tag="1.29.3")
    try:
        assert image.is_present()
    finally:
        image.rmi(force=True)


def test_pull_never(buildah_backend):
    with pytest.raises(subprocess.CalledProcessError):
        buildah_backend.ImageClass._inspect("busybox:1.25.1")
    image = buildah_backend.ImageClass("docker.io/library/busybox", tag="1.29.3",
                                       pull_policy=BuildahImagePullPolicy.NEVER)
    assert not image.is_present()


def test_list_containers(buildah_backend):
    image = buildah_backend.ImageClass(
        FEDORA_MINIMAL_REPOSITORY,
        tag=FEDORA_MINIMAL_REPOSITORY_TAG,
        pull_policy=BuildahImagePullPolicy.NEVER)
    container_name = random_str()
    c = image.run_via_binary(
        BuildahRunBuilder(
            additional_opts=[
                '--name', container_name
            ])
    )
    try:
        container_list = buildah_backend.list_containers()
        l = len(container_list)
        assert l >= 1
        cont_under_test = [x for x in container_list
                           if x.metadata.name == container_name][0]
        assert cont_under_test.metadata.image
        assert cont_under_test.metadata.image.get_full_name() == FEDORA_MINIMAL_IMAGE
        assert cont_under_test.metadata.command
    finally:
        c.delete(force=True)


def test_list_images(buildah_backend):
    image_list = buildah_backend.list_images()
    assert len(image_list) > 0
    # id of registry.fedoraproject.org/fedora-minimal:26
    assert isinstance(image_list[0], BuildahImage)
    assert image_list[0].get_id()
    assert image_list[0].get_full_name()
    assert image_list[0].is_present()


def test_image_metadata(buildah_backend):
    image = buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    im_metadata = image.get_metadata()

    assert im_metadata.command == ["/bin/bash"]
    assert im_metadata.name == FEDORA_MINIMAL_IMAGE
    assert im_metadata.env_variables["FGC"] == "f26"
    assert im_metadata.env_variables["DISTTAG"] == "f26container"
    assert im_metadata.labels == {}


def test_container_metadata(buildah_backend):
    image = buildah_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    c = image.run_via_binary(
        BuildahRunBuilder(
            additional_opts=[
                '--name', 'mycontainer',
            ])
    )

    try:
        container_metadata = c.get_metadata()

        assert container_metadata.command == ["/bin/bash"]
        assert container_metadata.name == "mycontainer"
        assert container_metadata.env_variables["FGC"] == "f26"
        assert container_metadata.env_variables["DISTTAG"] == "f26container"
        assert container_metadata.labels == {}
    finally:
        c.delete(force=True)

from __future__ import print_function, unicode_literals

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
    FEDORA_REPOSITORY

from conu.backend.podman.backend import PodmanBackend
from conu.backend.podman.container import PodmanRunBuilder, PodmanContainer
from conu.backend.podman.image import PodmanImagePullPolicy
from conu.backend.podman.client import get_client

from conu import ConuException

from six import string_types

import pytest


def test_api():
    """
    Test of python podman API
    """
    import podman
    with podman.Client() as client:
        list(map(print, client.images.list()))


def test_client():
    """
    Test of get_client()
    """
    with get_client() as client:
        assert client.system.ping()


def test_image():
    """
    Basic tests of interacting with image: inspect, tag, remove
    """
    with PodmanBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        assert "%s:%s" % (FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG) in image.inspect()['repotags']
        assert "containerconfig" in image.inspect()
        assert 'containerconfig' in image.inspect()
        assert "fedora-minimal:26" in image.get_full_name()
        assert "registry.fedoraproject.org/fedora-minimal:26" == str(image)
        assert "PodmanImage(repository=%s, tag=%s)" % (FEDORA_MINIMAL_REPOSITORY,
                                                       FEDORA_MINIMAL_REPOSITORY_TAG) == repr(image)
        assert isinstance(image.get_id(), string_types)
        new_image = image.tag_image(tag="test")
        new_image.rmi(via_name=True)
        assert not new_image.is_present()


def test_image_wrong_types():
    with PodmanBackend() as backend:
        with pytest.raises(ConuException) as exc:
            backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, PodmanImagePullPolicy.NEVER)
            assert "tag" in exc.value.message


def test_container():
    """
    Basic tests of interacting with a podman container
    """
    with PodmanBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        c = image.run_via_binary(
            PodmanRunBuilder(command=["cat"], additional_opts=["-i", "-t"])
        )
        try:
            assert c.is_running()
            assert "config" in c.inspect()
            assert "config" in c.inspect()
            assert c.get_id() == str(c)
            assert repr(c)
            assert isinstance(c.get_id(), string_types)
        finally:
            c.delete(force=True)


# def test_copy_to(tmpdir):
#     content = b"gardener did it"
#     p = tmpdir.join("secret")
#     p.write(content)
#
#     with PodmanBackend() as backend:
#         image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
#         c = image.run_via_binary(
#             command=["cat"], additional_opts=["-i", "-t"]
#         )
#         try:
#             assert c.is_running()
#             c.copy_to(str(p), "/")
#             assert [content] == c.execute(["cat", "/secret"])
#         finally:
#             c.delete(force=True)

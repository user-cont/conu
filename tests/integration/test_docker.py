# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import subprocess
import time

import pytest

from .constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, THE_HELPER_IMAGE, \
    FEDORA_REPOSITORY

from conu import DockerImage, DockerRunBuilder, Probe, ConuException

from six import string_types


def test_image():
    """
    Basic tests of interacting with image: inspect, tag, remove
    """
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    assert "Config" in image.inspect()
    assert "Config" in image.get_metadata()
    assert "fedora-minimal:26" in image.get_full_name()
    assert "registry.fedoraproject.org/fedora-minimal:26" == str(image)
    assert "DockerImage(repository=%s, tag=%s)" % (FEDORA_MINIMAL_REPOSITORY,
                                                   FEDORA_MINIMAL_REPOSITORY_TAG) == repr(image)
    assert isinstance(image.get_id(), string_types)
    new_image = image.tag_image(tag="test")
    new_image.rmi(via_name=True)


def test_container():
    """
    Basic tests of interacting with a container
    """
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    c = image.run_via_binary(
        DockerRunBuilder(command=["cat"], additional_opts=["-i", "-t"])
    )
    try:
        assert "Config" in c.inspect()
        assert "Config" in c.get_metadata()
        assert c.get_id() == str(c)
        assert repr(c)
        assert isinstance(c.get_id(), string_types)
    finally:
        c.stop()
        c.delete()


def test_copy_to(tmpdir):
    content = b"gardener did it"
    p = tmpdir.join("secret")
    p.write(content)

    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    c = image.run_via_binary(
        DockerRunBuilder(command=["cat"], additional_opts=["-i", "-t"])
    )
    try:
        c.copy_to(str(p), "/")
        assert content == c.execute(["cat", "/secret"])
    finally:
        c.stop()
        c.delete()


def test_copy_from(tmpdir):
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    c = image.run_via_binary(
        DockerRunBuilder(command=["cat"], additional_opts=["-i", "-t"])
    )
    try:
        c.copy_from("/etc/fedora-release", str(tmpdir))
        with open(os.path.join(str(tmpdir), "fedora-release")) as fd:
            assert fd.read() == "Fedora release 26 (Twenty Six)\n"

        c.copy_from("/etc", str(tmpdir))
        os.path.exists(os.path.join(str(tmpdir), "passwd"))
    finally:
        c.stop()
        c.delete()


def test_container_create_failed():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    # should raise an exc, there is no such command: waldo; we need to find waldo first
    with pytest.raises(ConuException):
        image.run_via_binary(
            DockerRunBuilder(command=["waldo"])
        )
    c = image.run_via_binary_in_foreground(
        DockerRunBuilder(command=["waldo"])
    )
    c.popen_instance.communicate()
    assert c.popen_instance.returncode > 0


def test_networking_scenario():
    """
    Listen via netcat in one container, send a secret message to the container via another one.
    """
    image = DockerImage(THE_HELPER_IMAGE)
    r1 = DockerRunBuilder(command=["nc", "-l", "-k", "0.0.0.0", "1234"])
    cont = image.run_via_binary(r1)
    # FIXME: wait
    time.sleep(0.2)
    assert cont.is_running()
    assert cont.get_IPv4s()
    assert cont.is_port_open(1234)
    assert not cont.is_port_open(2345)

    secret_text = b"gardener-did-it"

    r2 = DockerRunBuilder(command=["nc", cont.get_IPv4s()[0], "1234"])
    r2.options = ["-i", "--rm"]
    cont2 = image.run_via_binary_in_foreground(
        r2, popen_params={"stdin": subprocess.PIPE}, container_name="test-container")
    # FIXME: wait
    time.sleep(1)
    assert "" == cont.logs().decode("utf-8").strip()
    assert cont2.is_running()
    assert cont.is_running()
    cont2.popen_instance.communicate(input=secret_text + b"\n")
    # give container time to process
    time.sleep(1)
    cont.stop()
    assert not cont2.is_running()
    assert not cont.is_running()
    assert secret_text == cont.logs().strip()
    cont.delete()


def test_http_client():
    image = DockerImage(FEDORA_REPOSITORY)
    c = image.run_via_binary(
        DockerRunBuilder(command=["python3", "-m", "http.server", "--bind", "0.0.0.0 8000"])
    )
    c.start()
    time.sleep(1)  # FIXME: replace by wait once available
    assert c.is_running()
    r = c.http_request(port="8000")
    assert "<!DOCTYPE HTML PUBLIC" in r.content.decode("utf-8")
    assert r.ok
    r2 = c.http_request(path="/etc", port="8000")
    assert "<!DOCTYPE HTML PUBLIC" in r2.content.decode("utf-8")
    assert "passwd" in r2.content.decode("utf-8")
    assert r2.ok
    c.stop()
    c.delete()


def test_wait_for_status():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunBuilder(command=['sleep', '2'])
    cont = image.run_via_binary(cmd)

    start = time.time()
    p = Probe(timeout=6, fnc=cont.get_status, expected_retval='exited')
    p.run()
    end = time.time() - start
    assert end > 2, "Probe should wait till container status is exited"
    assert end < 7, "Probe should end when container status is exited"


def test_exit_code():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunBuilder(command=['sleep', '2'])
    cont = image.run_via_binary(cmd)
    assert cont.is_running() and cont.exit_code() == 0
    p = Probe(timeout=5, fnc=cont.get_status, expected_retval='exited')
    p.run()

    assert not cont.is_running() and cont.exit_code() == 0
    cmd = DockerRunBuilder(command=['bash', '-c', "exit 42"])
    cont = image.run_via_binary(cmd)
    cont.wait()
    assert cont.exit_code() == 42

# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import subprocess
import time

import pytest

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
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
        c.delete(force=True)


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
        assert [content] == c.execute(["cat", "/secret"])
    finally:
        c.delete(force=True)


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
        c.delete(force=True)


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


def test_interactive_container():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    command = ["bash"]
    r = DockerRunBuilder(command=command, additional_opts=["-i"])
    cont = image.run_via_binary_in_foreground(
        r, popen_params={"stdin": subprocess.PIPE, "stdout": subprocess.PIPE})
    try:
        assert "" == cont.logs().decode("utf-8").strip()
        assert cont.is_running()
        time.sleep(0.1)
        cont.popen_instance.stdin.write(b"echo palacinky\n")
        cont.popen_instance.stdin.flush()
        time.sleep(0.2)
        assert b"palacinky" in cont.popen_instance.stdout.readline()
    finally:
        cont.delete(force=True)


def test_http_client():
    image = DockerImage(FEDORA_REPOSITORY)
    c = image.run_via_binary(
        DockerRunBuilder(command=["python3", "-m", "http.server", "--bind", "0.0.0.0 8000"])
    )
    try:
        c.wait_for_port(8000)
        assert c.is_running()
        r = c.http_request(port="8000")
        assert "<!DOCTYPE HTML PUBLIC" in r.content.decode("utf-8")
        assert r.ok
        r2 = c.http_request(path="/etc", port="8000")
        assert "<!DOCTYPE HTML PUBLIC" in r2.content.decode("utf-8")
        assert "passwd" in r2.content.decode("utf-8")
        assert r2.ok
    finally:
        c.delete(force=True)


def test_wait_for_status():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunBuilder(command=['sleep', '2'])
    cont = image.run_via_binary(cmd)

    try:
        start = time.time()
        p = Probe(timeout=6, fnc=cont.get_status, expected_retval='exited')
        p.run()
        end = time.time() - start
        assert end > 2, "Probe should wait till container status is exited"
        assert end < 7, "Probe should end when container status is exited"
    finally:
        cont.delete(force=True)


def test_exit_code():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunBuilder(command=['sleep', '2'])
    cont = image.run_via_binary(cmd)
    try:
        assert cont.is_running() and cont.exit_code() == 0
        p = Probe(timeout=5, fnc=cont.get_status, expected_retval='exited')
        p.run()
        assert not cont.is_running() and cont.exit_code() == 0
    finally:
        cont.delete(force=True)

    cmd = DockerRunBuilder(command=['bash', '-c', "exit 42"])
    cont = image.run_via_binary(cmd)
    try:
        cont.wait()
        assert cont.exit_code() == 42
    finally:
        cont.delete(force=True)


def test_blocking_execute():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunBuilder(command=['sleep', 'infinity'])
    cont = image.run_via_binary(cmd)
    cont.execute(["bash", "-c", "exit 0"])
    assert [b"asd"] == cont.execute(["printf", "asd"])
    assert [b"asd\nasd"] == cont.execute(["printf", "asd\nasd"])
    with pytest.raises(ConuException) as ex:
        cont.execute(["bash", "-c", "exit 110"])
        assert "exit code 110" in ex.value.message
        assert "bash" in ex.value.message


def test_nonblocking_execute():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunBuilder(command=['sleep', 'infinity'])
    cont = image.run_via_binary(cmd)
    stream = cont.execute(["bash", "-c", "exit 0"], blocking=False)
    list(stream)
    gen = cont.execute(["printf", "asd"], blocking=False)
    assert [b"asd"] == list(gen)
    gen = cont.execute(["printf", "asd\nasd"], blocking=False)
    assert [b"asd\nasd"] == list(gen)
    cont.execute(["bash", "-c", "sleep 0.01; exit 110"], blocking=False)

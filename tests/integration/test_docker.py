# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import subprocess
import time

from .constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, THE_HELPER_IMAGE, \
    FEDORA_REPOSITORY

from conu.backend.docker import DockerContainer, DockerImage
from conu.backend.docker.container import DockerRunCommand
from conu.utils.probes import Probe

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
    c = DockerContainer.run_via_binary(
        image,
        DockerRunCommand(command=["cat"], additional_opts=["-i", "-t"])
    )
    assert "Config" in c.inspect()
    assert "Config" in c.get_metadata()
    assert c.get_id() == str(c)
    assert repr(c)
    assert isinstance(c.get_id(), string_types)
    c.stop()
    c.rm()


def test_networking_scenario():
    """
    Listen via netcat in one container, send a secret message to the container via another one.
    """
    image = DockerImage(THE_HELPER_IMAGE)
    r1 = DockerRunCommand(command=["nc", "-l", "-k", "0.0.0.0", "1234"])
    cont = DockerContainer.run_via_binary(image, r1)
    # FIXME: wait
    time.sleep(0.2)
    assert cont.is_running()
    assert cont.get_IPv4s()
    assert cont.is_port_open(1234)
    assert not cont.is_port_open(2345)

    secret_text = b"gardener-did-it"

    r2 = DockerRunCommand(command=["nc", cont.get_IPv4s()[0], "1234"])
    r2.options = ["-i", "--rm"]
    cont2 = DockerContainer.run_via_binary_in_foreground(
        image, r2, popen_params={"stdin": subprocess.PIPE}, container_name="test-container")
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
    cont.rm()


def test_http_client():
    image = DockerImage(FEDORA_REPOSITORY)
    c = DockerContainer.run_via_binary(
        image,
        DockerRunCommand(command=["python3", "-m", "http.server", "--bind", "0.0.0.0 8000"])
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
    c.rm()


def test_wait_for_status():
    image = DockerImage(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = DockerRunCommand(command=['sleep', '2'])
    cont = DockerContainer.run_via_binary(image, cmd)

    start = time.time()
    p = Probe(timeout=6, fnc=cont.get_status, expected_retval='exited')
    p.run()
    end = time.time() - start
    assert end > 2, "Probe should wait till container status is exited"
    assert end < 7, "Probe should end when container status is exited"

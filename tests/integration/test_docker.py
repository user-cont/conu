#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
TODO: create unit tests, mock interaction with docker
"""

import subprocess
import time

from conu.backend.docker import DockerContainer, DockerImage
from conu.utils.core import run_cmd
from nose.tools import assert_raises


def test_image():
    """
    Basic tests of interacting with image: pull, inspect, tag, remove
    """
    image1 = DockerImage("fedora")
    # FIXME: use busybox in integration tests, pull it before testing
    image1.pull()
    assert "Config" in image1.inspect()
    assert "fedora:latest" in image1.full_name()
    assert "fedora:latest" == str(image1)
    assert "Image(repository=fedora, tag=latest)" == repr(image1)
    image1.tag_image(tag="test")
    DockerImage.rmi("fedora:test")


def test_docker():
    """
    Use two images, use them as base for two different containers.
    cont1 is container what does start, will not finish immeadiately
       install package nc inside
       run nc server inside on port 1234
       from host send the message to ip address and port of cont1
       check if message in host arrived

    cont2 run just simple "ls /" command and finish immediatelly
         via assert there is check that sbin is output of command

    :return:
    """
    image1 = DockerImage("fedora")
    image1.pull()
    # complex case
    cont1 = DockerContainer(image1)
    cont1.start("/bin/bash")
    assert "Config" in cont1.inspect()
    assert cont1.check_running()
    assert "172" in cont1.get_IPv4s()[0]
    assert "sbin" in cont1.execute("ls /")
    cont1.install_packages("nc")
    bckgrnd = cont1.execute("nc -l 1234", raw=True, stdout=subprocess.PIPE)
    time.sleep(1)
    bckgrnd2 = run_cmd(["nc", cont1.get_IPv4s()[0], "1234"], raw=True, stdin=subprocess.PIPE)
    bckgrnd2.communicate(input="ahoj")
    assert "ahoj" in bckgrnd.communicate()[0]
    cont1.stop()
    cont1.clean()
    # simplier case
    cont2 = DockerContainer(image1)
    assert "sbin" in cont2.run("ls /")
    # test if raise is raised in case nonexisting command
    assert_raises(subprocess.CalledProcessError, cont2.run, "nonexisting command")

    # test if raise is raised in case bad volume mapping
    assert_raises(subprocess.CalledProcessError, cont2.run, "ls /", docker_params="-v abc:cba")


def test_read_file():
    i = DockerImage("fedora", tag="26")
    # i.pull()
    c = DockerContainer(i)
    c.start("sleep infinity")
    time.sleep(1)  # FIXME: replace by wait once available
    assert c.check_running()
    content = c.read_file("/etc/system-release")
    assert content == "Fedora release 26 (Twenty Six)\n"
    assert isinstance(content, str)
    assert_raises(subprocess.CalledProcessError, c.read_file, "/i/lost/my/banana")


def test_http_client():
    i = DockerImage("fedora", tag="26")
    # i.pull()
    c = DockerContainer(i)
    c.start("python3 -m http.server --bind 0.0.0.0 8000")
    time.sleep(1)  # FIXME: replace by wait once available
    assert c.check_running()
    r = c.http_request(port="8000")
    assert "<!DOCTYPE HTML PUBLIC" in r.content
    assert r.ok
    r2 = c.http_request(path="/etc", port="8000")
    assert "<!DOCTYPE HTML PUBLIC" in r2.content
    assert "passwd" in r2.content
    assert r2.ok


if __name__ == "__main__":
    test_image()
    test_docker()

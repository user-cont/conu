#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
TODO: create dir tests/integration and move this file over there as docker_test.py
      create unit tests, mock interaction with docker
"""

import subprocess
import time

from conu.docker.core import Image, Container
from conu.utils.core import run_cmd
from nose.tools import assert_raises


def test_image():
    """
    Basic tests of interacting with image: pull, inspect, tag, remove
    """
    i = Image("fedora", tag="26")
    # FIXME: use busybox in integration tests, pull it before testing
    i.pull()
    assert "Config" in i.inspect()
    assert "fedora:26" == i.full_name()
    assert "fedora:26" == str(i)
    assert "Image(repository=fedora, tag=26)" == repr(i)
    i.tag_image(tag="test")
    Image.rmi("fedora:test")


def test_container():
    """
    Test case:
       install package nc inside
       run nc server inside on port 1234
       from host send the message to ip address and port of cont1  # FIXME: requires nc on host
       check if message in host arrived

    :return:
    """
    i = Image("fedora", tag="26")
    i.pull()
    # complex case
    cont1 = Container.run_using_docker_client(i, docker_run_params="-i", command="cat")
    assert "Config" in cont1.inspect()
    assert cont1.is_running()
    assert cont1.get_ip()
    assert "usr" in cont1.execute("ls /", shell=False)
    # FIXME: this is really expensive
    cont1.execute("dnf install -y nc", shell=False)
    bckgrnd = cont1.execute("nc -l 1234", raw=True, stdout=subprocess.PIPE, shell=False)
    time.sleep(1)
    bckgrnd2 = run_cmd(["nc", cont1.get_ip(), "1234"], raw=True, stdin=subprocess.PIPE)
    bckgrnd2.communicate(input="ahoj")
    assert "ahoj" in bckgrnd.communicate()[0]
    # test if raise is raised in case nonexisting command
    assert_raises(subprocess.CalledProcessError, cont1.execute, "nonexisting command")
    cont1.stop()
    cont1.rm()


def test_read_file():
    i = Image("fedora", tag="26")
    i.pull()
    c = Container.run_using_docker_client(i, command="sleep infinity")
    # we need to wait
    time.sleep(1)
    assert c.is_running()
    content = c.read_file("/etc/system-release")
    assert content == "Fedora release 26 (Twenty Six)\n"
    assert isinstance(content, str)
    assert_raises(subprocess.CalledProcessError, c.read_file, "/i/lost/my/banana")
    c.stop()
    c.rm()


if __name__ == "__main__":
    test_image()
    test_container()
    test_read_file()

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
    image1 = Image("fedora")
    # FIXME: use busybox in integration tests, pull it before testing
    image1.pull()
    assert "Config" in image1.inspect()
    assert "fedora:latest" in image1.full_name()
    assert "fedora:latest" == str(image1)
    assert "Image(repository=fedora, tag=latest)" == repr(image1)
    image1.tag_image(tag="test")
    Image.rmi("fedora:test")


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
    image1 = Image("fedora")
    image1.pull()
    # complex case
    cont1 = Container(image1)
    cont1.start("/bin/bash")
    assert "Config" in cont1.inspect()
    assert cont1.check_running()
    assert "172" in cont1.get_ip()
    assert "sbin" in cont1.execute("ls /")
    cont1.install_packages("nc")
    bckgrnd = cont1.execute("nc -l 1234", raw=True, stdout=subprocess.PIPE)
    time.sleep(1)
    bckgrnd2 = run_cmd(["nc", cont1.get_ip(), "1234"], raw=True, stdin=subprocess.PIPE)
    bckgrnd2.communicate(input="ahoj")
    assert "ahoj" in bckgrnd.communicate()[0]
    cont1.stop()
    cont1.clean()
    # simplier case
    cont2 = Container(image1)
    assert "sbin" in cont2.run("ls /")
    # test if raise is raised in case nonexisting command
    assert_raises(subprocess.CalledProcessError, cont2.run, "nonexisting command")

    # test if raise is raised in case bad volume mapping
    assert_raises(subprocess.CalledProcessError, cont2.run, "ls /", docker_params="-v abc:cba")

if __name__ == "__main__":
    test_image()
    test_docker()

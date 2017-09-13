#!/usr/bin/python
# -*- coding: utf-8 -*-


from core import *
from nose.tools import assert_raises


def test_image():
    """
    Image tests. Pull image. check it is able to inspect it

    :return:
    """
    image1 = Image("fedora", tag="ahoj")
    assert "Config" in image1.inspect()
    assert "fedora" in image1.get_image_name()
    assert "ahoj" in image1.get_tag_name()
    assert "ahoj" == str(image1)
    image1.clean()


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
    image1 = Image("fedora", tag="ahoj")
    image2 = Image("fedora", tag="hallo")
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
    cont2 = Container(image2)
    assert "sbin" in cont2.run("ls /")
    # test if raise is raised in case nonexisting command
    assert_raises(subprocess.CalledProcessError, cont2.run, "nonexisting command")

    # test if raise is raised in case bad volume mapping
    assert_raises(subprocess.CalledProcessError, cont2.run, "ls /", docker_params="-v abc:cba")

if __name__ == "__main__":
    test_image()
    test_docker()

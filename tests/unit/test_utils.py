# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import subprocess

import pytest

from conu import ConuException, random_str, Directory


def test_random_str():
    assert random_str()
    assert random_str() != random_str()
    assert len(random_str(size=42)) == 42
    assert len(random_str(2)) == 2


def test_directory_basic():
    with Directory(os.path.join("/tmp/", random_str())) as d:
        with open(os.path.join(str(d), "file"), "w") as fd:
            fd.write("hi!")
        with open(os.path.join(str(d), "file")) as fd:
            assert fd.read() == "hi!"
    assert not os.path.isdir(str(d))


def test_directory_mode():
    p = os.path.join("/tmp/", random_str())
    d = Directory(p, mode=0o0700)
    try:
        d.initialize()
        m = os.stat(p).st_mode
        print(m)
        assert oct(m)[-4:] == "0700"
    finally:
        d.clean()
    assert not os.path.isdir(p)


def test_directory_selinux_bad():
    selinux_type = "voodoo_file_t"
    selinux_context = "janko_u:beer_r:spilled_all_over_the_table_t:s0"
    p = os.path.join("/tmp/", random_str())
    with pytest.raises(ConuException):
        Directory(p, selinux_type=selinux_type, selinux_context=selinux_context)
    assert not os.path.isdir(p)


@pytest.mark.selinux
def test_directory_selinux_type():
    selinux_type = "container_file_t"
    p = os.path.join("/tmp/", random_str())
    with Directory(p, selinux_type=selinux_type):
        output = subprocess.check_output(["ls", "-Z", "-1", "-d", p])
        assert selinux_type in output.decode("utf-8")
    assert not os.path.isdir(p)


@pytest.mark.selinux
def test_directory_selinux_context():
    selinux_context = "system_u:object_r:unlabeled_t:s0"
    p = os.path.join("/tmp/", random_str())
    with Directory(p, selinux_context=selinux_context):
        output = subprocess.check_output(["ls", "-Z", "-1", "-d", p])
        assert selinux_context in output.decode("utf-8")
    assert not os.path.isdir(p)


def test_directory_acl():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, facl_rules=["u:26:rwx"]) as d:
        x = subprocess.check_output(["getfacl", str(d)]).decode("utf-8")
        assert "user:26:rwx" in x.split("\n")
    assert not os.path.isdir(str(d))


def test_user_ownership_int():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, user_owner=99) as d:
        s = os.stat(d.path)
        assert s.st_uid == 99


def test_user_ownership_str():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, user_owner="nobody") as d:
        s = os.stat(d.path)
        assert s.st_uid == 99


def test_user_ownership_404():
    p = os.path.join("/tmp/", random_str())
    with pytest.raises(ConuException):
        Directory(p, user_owner="waldo")


def test_group_ownership():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, group_owner=99) as d:
        s = os.stat(d.path)
        assert s.st_gid == 99


def test_group_ownership_str():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, group_owner="nobody") as d:
        s = os.stat(d.path)
        assert s.st_gid == 99


def test_group_ownership_404():
    p = os.path.join("/tmp/", random_str())
    with pytest.raises(ConuException):
        Directory(p, group_owner="illuminati")


def test_ownership():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, user_owner="nobody", group_owner="nobody") as d:
        s = os.stat(d.path)
        assert s.st_gid == 99
        assert s.st_uid == 99

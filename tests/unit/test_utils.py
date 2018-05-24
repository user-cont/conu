# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import print_function, unicode_literals

import os
import subprocess

import pytest

from conu import ConuException, random_str, Directory
from conu.utils import graceful_get
from conu.utils.filesystem import Volume
from conu.utils.http_client import get_url


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
    with Directory(p, user_owner=65534) as d:
        s = os.stat(d.path)
        assert s.st_uid == 65534


def test_user_ownership_str():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, user_owner="nobody") as d:
        s = os.stat(d.path)
        assert s.st_uid == 65534


def test_user_ownership_404():
    p = os.path.join("/tmp/", random_str())
    with pytest.raises(ConuException):
        Directory(p, user_owner="waldo")


def test_group_ownership():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, group_owner=65534) as d:
        s = os.stat(d.path)
        assert s.st_gid == 65534


def test_group_ownership_str():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, group_owner="nobody") as d:
        s = os.stat(d.path)
        assert s.st_gid == 65534


def test_group_ownership_404():
    p = os.path.join("/tmp/", random_str())
    with pytest.raises(ConuException):
        Directory(p, group_owner="illuminati")


def test_ownership():
    p = os.path.join("/tmp/", random_str())
    with Directory(p, user_owner="nobody", group_owner="nobody") as d:
        s = os.stat(d.path)
        assert s.st_gid == 65534
        assert s.st_uid == 65534


def test_graceful_get():
    assert graceful_get({"a": [{1: 2}, {"b": "c"}]}, "a", 1, "b") == "c"


def test_http_client_get_url():
    assert get_url(path="/", host="172.1.1.1", port=80) == "http://172.1.1.1:80/"
    assert get_url(path="/app",
                   host="domain.example.org",
                   port=443) == "http://domain.example.org:443/app"


@pytest.mark.parametrize("input_parameter,result", [
    ("/target/path", "/target/path"),
    (("/source/path", "/target/path"), "/source/path:/target/path"),
    (("/source/path", "/target/path", "mode"), "/source/path:/target/path:mode"),
    ((Directory("/source/path"), "/target/path"), "/source/path:/target/path"),
    ((Directory("/source/path"), "/target/path", "mode"), "/source/path:/target/path:mode"),
])
def test_volume_create_from_tuple(input_parameter, result):
    assert str(Volume.create_from_tuple(input_parameter)) == result


@pytest.mark.parametrize("source,target,mode,result", [
    (None, "/target/path", None, "/target/path"),
    ("/source/path", "/target/path", None, "/source/path:/target/path"),
    ("/source/path", "/target/path", "mode", "/source/path:/target/path:mode"),
    (Directory("/source/path"), "/target/path", None, "/source/path:/target/path"),
    (Directory("/source/path"), "/target/path", "mode", "/source/path:/target/path:mode"),
])
def test_volume_init(source, target, mode, result):
    assert str(Volume(source=source,
                      target=target,
                      mode=mode)) == result


@pytest.mark.parametrize("instance,result", [
    (Volume("/target/path"), "/target/path"),
    (Volume("/target/path", "/source/path"), "/source/path:/target/path"),
    (Volume("/target/path", "/source/path", "mode"), "/source/path:/target/path:mode"),
    (Volume("/target/path", Directory("/source/path")), "/source/path:/target/path"),
    (Volume("/target/path", Directory("/source/path"), "mode"), "/source/path:/target/path:mode"),
])
def test_volume_init_raw(instance, result):
    assert str(instance) == result

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
import time

import docker.errors
import pytest

from conu.backend.docker.backend import parse_reference
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
    FEDORA_REPOSITORY

from conu.apidefs.metadata import ContainerStatus
from conu.backend.docker.client import get_client
from conu import \
    DockerRunBuilder, \
    Probe, \
    ConuException, \
    DockerBackend, \
    DockerImagePullPolicy, \
    Directory

from six import string_types


@pytest.mark.parametrize("reference,result", [
    ("registry.fedoraproject.org/fedora:27", ("registry.fedoraproject.org/fedora", "27")),
    ("registry.fedoraproject.org/fedora", ("registry.fedoraproject.org/fedora", "latest")),
    ("registry.fedoraproject.org:7890/fedora",
     ("registry.fedoraproject.org:7890/fedora", "latest")),
])
def test_parse_reference(reference, result):
    assert parse_reference(reference) == result


def test_image():
    """
    Basic tests of interacting with image: inspect, tag, remove
    """
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        assert "Config" in image.inspect()
        assert "Config" in image.inspect()
        assert "fedora-minimal:26" in image.get_full_name()
        assert "registry.fedoraproject.org/fedora-minimal:26" == str(image)
        assert "DockerImage(repository=%s, tag=%s)" % (FEDORA_MINIMAL_REPOSITORY,
                                                       FEDORA_MINIMAL_REPOSITORY_TAG) == repr(image)
        assert isinstance(image.get_id(), string_types)
        new_image = image.tag_image(tag="test")
        new_image.rmi(via_name=True)


def test_image_wrong_types():
    with DockerBackend() as backend:
        with pytest.raises(ConuException) as exc:
            backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, DockerImagePullPolicy.NEVER)
            assert "tag" in exc.value.message


def test_container():
    """
    Basic tests of interacting with a container
    """
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        c = image.run_via_binary(
            DockerRunBuilder(command=["cat"], additional_opts=["-i", "-t"])
        )
        try:
            assert "Config" in c.inspect()
            assert "Config" in c.inspect()
            assert c.get_id() == str(c)
            assert repr(c)
            assert isinstance(c.get_id(), string_types)
        finally:
            c.delete(force=True)


def test_copy_to(tmpdir):
    content = b"gardener did it"
    p = tmpdir.join("secret")
    p.write(content)

    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        c = image.run_via_binary(
            command=["cat"], additional_opts=["-i", "-t"]
        )
        try:
            c.copy_to(str(p), "/")
            assert [content] == c.execute(["cat", "/secret"])
        finally:
            c.delete(force=True)


def test_copy_from(tmpdir):
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        c = image.run_via_binary(
            command=["cat"], additional_opts=["-i", "-t"]
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
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        # should raise an exc, there is no such command: waldo; we need to find waldo first
        with pytest.raises(ConuException):
            image.run_via_binary(
                command=["waldo"]
            )
        c = image.run_via_binary_in_foreground(
            DockerRunBuilder(command=["waldo"])
        )
        c.popen_instance.communicate()
        assert c.popen_instance.returncode > 0


def test_interactive_container():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        command = ["bash"]
        additional_opts = ["-i"]
        cont = image.run_via_binary_in_foreground(
            command=command, additional_opts=additional_opts,
            popen_params={"stdin": subprocess.PIPE, "stdout": subprocess.PIPE}
        )
        try:
            assert "" == cont.logs_unicode()
            assert cont.is_running()
            time.sleep(0.1)
            cont.popen_instance.stdin.write(b"echo palacinky\n")
            cont.popen_instance.stdin.flush()
            time.sleep(0.2)
            assert b"palacinky" in cont.popen_instance.stdout.readline()
        finally:
            cont.delete(force=True)


def test_container_logs():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        command = ["bash", "-c", "for x in `seq 1 5`; do echo $x; done"]
        cont = image.run_via_binary(command=command)
        try:
            Probe(timeout=5, fnc=cont.get_status, expected_retval='exited').run()
            assert not cont.is_running()
            assert list(cont.logs()) == [b"1\n", b"2\n", b"3\n", b"4\n", b"5\n"]
            assert cont.logs_unicode() == "1\n2\n3\n4\n5\n"
            assert cont.logs_in_bytes() == b"1\n2\n3\n4\n5\n"
        finally:
            cont.delete(force=True)


def test_http_client():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_REPOSITORY)
        c = image.run_via_binary(
            command=["python3", "-m", "http.server", "--bind", "0.0.0.0 8000"]
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


def test_http_client_context():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_REPOSITORY)
        c = image.run_via_binary(
            command=["python3", "-m", "http.server", "--bind", "0.0.0.0 8000"]
        )
        try:
            c.wait_for_port(8000)
            with c.http_client(port=8000) as session:
                r = session.get("/")
                assert r.ok
                assert "<!DOCTYPE HTML PUBLIC" in r.content.decode("utf-8")

                r2 = session.get("/etc")
                assert "<!DOCTYPE HTML PUBLIC" in r2.content.decode("utf-8")
                assert "passwd" in r2.content.decode("utf-8")
                assert r2.ok
        finally:
            c.delete(force=True)


def test_wait_for_status():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        cmd = ['sleep', '2']
        cont = image.run_via_binary(command=cmd)

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
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        cmd = ['sleep', '2']
        cont = image.run_via_binary(command=cmd)
        try:
            assert cont.is_running() and cont.exit_code() == 0
            p = Probe(timeout=5, fnc=cont.get_status, expected_retval='exited')
            p.run()
            assert not cont.is_running() and cont.exit_code() == 0
        finally:
            cont.delete(force=True)

        cmd = ['bash', '-c', "exit 42"]
        cont = image.run_via_binary(command=cmd)
        try:
            cont.wait()
            assert cont.exit_code() == 42
        finally:
            cont.delete(force=True)


def test_blocking_execute():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        cmd = ['sleep', 'infinity']
        cont = image.run_via_binary(command=cmd)
        cont.execute(["bash", "-c", "exit 0"])
        assert [b"asd"] == cont.execute(["printf", "asd"])
        assert [b"asd\nasd"] == cont.execute(["printf", "asd\nasd"])
        with pytest.raises(ConuException) as ex:
            cont.execute(["bash", "-c", "exit 110"])
            assert "exit code 110" in ex.value.message
            assert "bash" in ex.value.message


def test_nonblocking_execute():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        cmd = ['sleep', 'infinity']
        cont = image.run_via_binary(command=cmd)
        stream = cont.execute(["bash", "-c", "exit 0"], blocking=False)
        list(stream)
        gen = cont.execute(["printf", "asd"], blocking=False)
        assert [b"asd"] == list(gen)
        gen = cont.execute(["printf", "asd\nasd"], blocking=False)
        assert [b"asd\nasd"] == list(gen)
        cont.execute(["bash", "-c", "sleep 0.01; exit 110"], blocking=False)


def test_pull_always():
    with DockerBackend() as backend:
        image = backend.ImageClass("docker.io/library/busybox", tag="1.25.1",
                                   pull_policy=DockerImagePullPolicy.ALWAYS)
        try:
            assert image.is_present()
        finally:
            image.rmi(force=True)


def test_pull_if_not_present():
    with DockerBackend() as backend:
        with pytest.raises(docker.errors.DockerException):
            get_client().inspect_image("docker.io/library/busybox:1.25.1")
        image = backend.ImageClass("docker.io/library/busybox", tag="1.25.1")
        try:
            assert image.is_present()
        finally:
            image.rmi(force=True)


def test_pull_never():
    with DockerBackend() as backend:
        with pytest.raises(docker.errors.DockerException):
            get_client().inspect_image("docker.io/library/busybox:1.25.1")
        image = backend.ImageClass("docker.io/library/busybox", tag="1.25.1",
                                   pull_policy=DockerImagePullPolicy.NEVER)
        assert not image.is_present()


def test_set_name():
    with DockerBackend() as backend:
        test_name = 'jondoe'
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                   pull_policy=DockerImagePullPolicy.NEVER)
        cont = image.run_via_binary()
        assert cont.name
        cont.delete(force=True)

        cont = image.run_via_binary_in_foreground()
        assert cont.name
        cont.delete(force=True)

        additional_opts = ['--name', test_name]
        cont = image.run_via_binary(additional_opts=additional_opts)
        assert cont.name == test_name
        cont.delete(force=True)

        additional_opts = ['--name', test_name]
        cont = image.run_via_binary_in_foreground(additional_opts=additional_opts)
        assert cont.name == test_name
        cont.delete(force=True)


def test_run_with_volumes_metadata_check():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                   pull_policy=DockerImagePullPolicy.NEVER)
        container = image.run_via_binary(volumes=(Directory('/usr/bin'), "/mountpoint", "Z"))

        binds = container.inspect ()["HostConfig"]["Binds"]
        assert "/usr/bin:/mountpoint:Z" in binds

        mount = container.inspect()["Mounts"][0]
        print(mount)
        assert mount["Source"] == "/usr/bin"
        assert mount["Destination"] == "/mountpoint"
        assert mount["Mode"] == "Z"

        container.delete(force=True)


def test_list_containers():
    with DockerBackend() as backend:
        l = len(backend.list_containers())
        assert l >= 0
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                   pull_policy=DockerImagePullPolicy.NEVER)
        container = image.run_via_binary(command=["sleep", "1"])
        try:
            container_list = backend.list_containers()
        finally:
            container.delete(force=True)
        l = len(container_list)
        assert l >= 1
        assert container_list[0].short_metadata
        assert container_list[0].short_metadata["Id"]


def test_list_images():
    with DockerBackend() as backend:
        image_list = backend.list_images()
        assert len(image_list) > 0
        assert image_list[0].short_metadata
        assert image_list[0].short_metadata["Id"]


def test_build_image():
    with DockerBackend() as backend:
        name = 'conu-test-image'
        integration_tests_dir = os.path.abspath(os.path.dirname(__file__))
        image_dir = os.path.join(integration_tests_dir, "data/greeter")

        image = backend.ImageClass.build(os.path.join(image_dir), tag=name)
        assert image.inspect()['RepoTags'][0] == name + ':latest'
        container = image.run_via_binary()
        assert container.logs_unicode() == 'Hello!\n'


def test_layers():
    with DockerBackend() as backend:
        image = backend.ImageClass('punchbag')
        layer_ids = image.get_layer_ids()
        layers = image.layers()

        assert len(layer_ids) == len(layers)
        for l in layers:
            assert l.inspect()["Id"] in layer_ids

        punchbag_cmd = [
                "/bin/sh",
                "-c",
                "#(nop) ",
                "CMD [\"usage\"]"
        ]
        assert layers[0].inspect()['ContainerConfig']['Cmd'] == punchbag_cmd
        rev = image.layers(rev=False)
        assert rev[-1].inspect()['ContainerConfig']['Cmd'] == punchbag_cmd


def test_metadata():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

        c = image.run_via_binary(
            DockerRunBuilder(command=["cat"], additional_opts=['-i',
                                                               '-t',
                                                               '--name', 'my_container',
                                                               '-p', '1234:12345',
                                                               '-p', '123:12345',
                                                               '-p', '8080',
                                                               '-p', '444:8080',
                                                               '--hostname', 'my_hostname',
                                                               '-e', 'ENV1=my_env',
                                                               '-e', 'ASD=',
                                                               '-e', 'A=B=C=D',
                                                               '-e', 'XYZ',
                                                               '-l', 'testlabel1=testvalue1'
                                                               ])
        )

        container_metadata = c.get_metadata()

        try:
            assert container_metadata.command == ["cat"]
            assert container_metadata.name == "my_container"
            assert container_metadata.env_variables["ENV1"] == "my_env"
            assert container_metadata.env_variables["ASD"] == ""
            assert container_metadata.env_variables["A"] == "B=C=D"
            assert container_metadata.hostname == "my_hostname"
            assert "XYZ" not in list(container_metadata.env_variables.keys())
            assert container_metadata.port_mappings == {'12345/tcp': [1234, 123], '8080/tcp': [None, 444]}
            assert container_metadata.exposed_ports == ["12345/tcp", "8080/tcp"]
            assert container_metadata.labels["testlabel1"] == "testvalue1"
            assert container_metadata.status == ContainerStatus.RUNNING
        finally:
            c.delete(force=True)

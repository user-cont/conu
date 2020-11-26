# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

from __future__ import print_function, unicode_literals

import os
import subprocess
import time

import docker.errors
import pytest

from flexmock import flexmock

from conu.utils import parse_reference
from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
    FEDORA_REPOSITORY, FEDORA_MINIMAL_IMAGE_REGEX, FEDORA_MINIMAL_NAME_REGEX

from conu.apidefs.metadata import ContainerStatus
from conu.backend.docker.client import get_client
from conu import \
    DockerRunBuilder, \
    Probe, \
    ConuException, \
    DockerBackend, \
    DockerImagePullPolicy, \
    Directory

from conu.backend.docker.skopeo import SkopeoTransport
from six import string_types

import re

@pytest.mark.parametrize("reference,result", [
    ("registry.fedoraproject.org/fedora:31", ("registry.fedoraproject.org/fedora", "31")),
    ("registry.fedoraproject.org/fedora", ("registry.fedoraproject.org/fedora", "latest")),
    ("registry.fedoraproject.org:7890/fedora",
     ("registry.fedoraproject.org:7890/fedora", "latest")),
])
def test_parse_reference(reference, result):
    assert parse_reference(reference) == result


def test_copy_basic(tmpdir):
    """
    Tests if copy does something
    :param tmpdir:
    """
    with DockerBackend() as backend:
        image = backend.ImageClass("docker.io/alpine",
                                   tag="latest",
                                   pull_policy=DockerImagePullPolicy.NEVER)
        assert "alpine" in image.get_full_name()
        image2 = image.skopeo_pull()
        assert image2.is_present()
        assert image2.transport == SkopeoTransport.DOCKER_DAEMON
        assert "Config" in image2.inspect()


def test_skopeo_pull_push():
    """
    test pulling with skope and if push call is not invalid
    """
    with DockerBackend() as backend:
        image = backend.ImageClass("docker.io/alpine",
                                   tag="latest",
                                   pull_policy=DockerImagePullPolicy.NEVER)
        pulled = image.skopeo_pull()
        assert pulled.is_present()

        with pytest.raises(ConuException):
            pulled.skopeo_push()

        (flexmock(pulled, skopeo_push=lambda: "pushed_image")
         .should_receive("skopeo_push").with_args("your_repo/alpine")
         .and_return("pushed_image"))


def test_copy_transports(tmpdir):
    """
    Tests copying trough different transports
    :param tmpdir:
    """
    with DockerBackend() as backend:
        image = backend.ImageClass("docker.io/alpine",
                                   tag="latest",
                                   pull_policy=DockerImagePullPolicy.NEVER)

        image2 = image.copy(target_transport=SkopeoTransport.DIRECTORY, target_path=str(tmpdir))
        image3 = image2.copy(source_path=str(tmpdir), target_transport=SkopeoTransport.DOCKER_DAEMON, tag="oldest")
        (flexmock(image3).should_receive("skopeo_push")
         .and_raise(ConuException, "There was and error while copying repository", image3.name))
        image4 = image3.copy(target_transport=SkopeoTransport.DOCKER_DAEMON)
        assert image4.is_present()
        yay = image3.copy("himalaya", target_transport=SkopeoTransport.DOCKER_DAEMON, source_path=str(tmpdir))
        assert yay.is_present()


def test_copy_save(tmpdir):
    """
    Tries to pull image, then remove it, and the pull it again, but with save_to
    check if save_to actually saves the object
    """
    with DockerBackend() as backend:
        image = backend.ImageClass("docker.io/alpine",
                                   tag="latest",
                                   pull_policy=DockerImagePullPolicy.IF_NOT_PRESENT)
        assert image.is_present()
        image_oci = image.copy(target_transport=SkopeoTransport.OCI, tag="3.7", target_path=str(tmpdir))
        assert image_oci.path == str(tmpdir), "copied image did not remember it's path"
        image.rmi(True, True)
        assert not image.is_present()

        image_oci.save_to(image)
        assert image.is_present()


def test_image():
    """
    Basic tests of interacting with image: inspect, tag, remove
    """
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        assert "Config" in image.inspect()
        assert "Config" in image.inspect()
        assert re.match(FEDORA_MINIMAL_IMAGE_REGEX, image.get_full_name())
        assert re.match(FEDORA_MINIMAL_IMAGE_REGEX, str(image))
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
                assert fd.read() == "Fedora release 31 (Thirty One)\n"

            c.copy_from("/etc", str(tmpdir))
            os.path.exists(os.path.join(str(tmpdir), "passwd"))
        finally:
            c.delete(force=True)


def test_container_create_failed():
    with DockerBackend(logging_level=10) as backend:
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
            command=["python3", "-m", "http.server", "--bind", "0.0.0.0", "8000"]
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
            command=["python3", "-m", "http.server", "--bind", "0.0.0.0", "8000"]
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


def test_run_with_volumes_metadata_check(tmpdir):
    with DockerBackend() as backend:
        t = str(tmpdir)
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                   pull_policy=DockerImagePullPolicy.NEVER)
        container = image.run_via_binary(volumes=(Directory(t), "/mountpoint", "Z"))

        binds = container.inspect()["HostConfig"]["Binds"]
        assert t + ":/mountpoint:Z" in binds

        mount = container.inspect()["Mounts"][0]
        assert mount["Source"] == t
        assert mount["Destination"] == "/mountpoint"
        assert mount["Mode"] == "Z"

        container.delete(force=True)


def test_list_containers():
    with DockerBackend() as backend:
        l = len(backend.list_containers())
        assert l >= 0
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                   pull_policy=DockerImagePullPolicy.NEVER)
        drb = DockerRunBuilder(command=["sleep", "1"], additional_opts=[
            "-e", "FOO=BAR",
            "-p", "1234"
        ])
        container = image.run_via_binary(run_command_instance=drb)
        try:
            container_list = backend.list_containers()
            l = len(container_list)
            assert l >= 1
            cont_under_test = [x for x in container_list
                               if x.metadata.identifier == container.get_id()][0]
            assert cont_under_test.metadata.image
            # TODO: implement parsing docker_client.containers metadata
            # assert cont_under_test.metadata.command
            # assert cont_under_test.metadata.env_variables == {"FOO": "BAR"}
            # assert cont_under_test.metadata.exposed_ports == ["1234"]
            # assert cont_under_test.get_IPv4s()
        finally:
            container.delete(force=True)


def test_list_images():
    with DockerBackend() as backend:
        image_list = backend.list_images()
        assert len(image_list) > 0
        the_id = "756d8881fb18271a1d55f6ee7e355aaf38fb2973f5fbb0416cf5de628624318b"
        image_under_test = [x for x in image_list if x.metadata.identifier == the_id][0]
        assert image_under_test.metadata.digest
        assert image_under_test.metadata.repo_digests


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


def test_container_metadata():
    with DockerBackend(logging_level=10) as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

        c = image.run_via_binary(
            DockerRunBuilder(command=["cat"], additional_opts=['-i',
                                                               '-t',
                                                               '--name', 'my_container',
                                                               '-p', '1234:12345',
                                                               '-p', '123:12345',
                                                               '-p', '8080',
                                                               '--hostname', 'my_hostname',
                                                               '-e', 'ENV1=my_env',
                                                               '-e', 'ASD=',
                                                               '-e', 'A=B=C=D',
                                                               '-e', 'XYZ',
                                                               '-l', 'testlabel1=testvalue1'
                                                               ])
        )

        try:
            container_metadata = c.get_metadata()

            assert container_metadata.command == ["cat"]
            assert container_metadata.name == "my_container"
            assert container_metadata.env_variables["ENV1"] == "my_env"
            assert container_metadata.env_variables["ASD"] == ""
            assert container_metadata.env_variables["A"] == "B=C=D"
            assert container_metadata.hostname == "my_hostname"
            assert "XYZ" not in list(container_metadata.env_variables.keys())
            assert '12345/tcp' in container_metadata.port_mappings
            assert container_metadata.port_mappings['12345/tcp'] == [1234, 123]
            assert '8080/tcp' in container_metadata.port_mappings
            assert container_metadata.exposed_ports == ["12345/tcp", "8080/tcp"]
            assert container_metadata.labels["testlabel1"] == "testvalue1"
            assert container_metadata.status == ContainerStatus.RUNNING
        finally:
            c.delete(force=True)


def test_image_metadata():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_REPOSITORY)

        image_metadata = image.get_metadata()

        assert image_metadata.command == image.inspect(refresh=True)['Config']['Cmd']
        assert image_metadata.creation_timestamp == image.inspect(refresh=True)['Created']
        assert image_metadata.identifier == image.inspect(refresh=True)['Id'].split(':')[1]
        assert image_metadata.labels == image.inspect(refresh=True)['Config']['Labels']
        assert image_metadata.name == image.inspect(refresh=True)['RepoTags'][0]

        # comparison with hard coded values that are unlikely to change with new versions of image
        assert image_metadata.command == ["/bin/bash"]
        assert image_metadata.labels['name'] == 'fedora'


def test_docker_parameters():
    docker_run_builder = DockerRunBuilder(additional_opts=['-l', 'hello=there', '-l', 'oh=noo', '--name', 'test', '-d',
                                                           '--hostname', 'my_hostname',
                                                           '--rm', '--privileged', '--isolation', 'default',
                                                           '--mac-address', '92:d0:c6:0a:29:33',
                                                           '--memory', '1G', '--user', 'my_user',
                                                           '--workdir', '/tmp',
                                                           '--env', 'ENV1=my_env', '-p', '123:12345', '-p', '1444',
                                                           '-p', '10.0.0.1::150', '-p', '10.0.0.2:2345:7654',
                                                           '--cap-add', 'MKNOD', '--cap-add', 'SYS_ADMIN',
                                                           '--cap-drop', 'SYS_ADMIN', '--device', '/dev/sdc:/dev/xvdc',
                                                           '--dns', 'www.example.com', '--group-add', 'group1',
                                                           '--group-add', 'group2', '--mount', '/tmp',
                                                           '--volume', '/tmp:/tmp', '--no-healthcheck'],
                                          command=['sleep', '50'])

    parameters = docker_run_builder.get_parameters()

    assert parameters.labels == {'hello': 'there', 'oh': 'noo'}
    assert parameters.name == 'test'
    assert parameters.detach
    assert parameters.privileged
    assert parameters.hostname == 'my_hostname'
    assert parameters.remove
    assert parameters.isolation == 'default'
    assert parameters.mac_address == '92:d0:c6:0a:29:33'
    assert parameters.mem_limit == '1G'
    assert parameters.user == 'my_user'
    assert parameters.working_dir == '/tmp'
    assert 'ENV1=my_env' in parameters.env_variables
    assert parameters.port_mappings == {'12345': 123, '1444': None, '150': ('10.0.0.1', None), '7654': ('10.0.0.2', 2345)}
    assert parameters.cap_add == ['MKNOD', 'SYS_ADMIN']
    assert parameters.cap_drop == ['SYS_ADMIN']
    assert parameters.devices == ['/dev/sdc:/dev/xvdc']
    assert parameters.dns == ['www.example.com']
    assert parameters.group_add == ['group1', 'group2']
    assert parameters.mounts == ['/tmp']
    assert parameters.volumes == ['/tmp:/tmp']
    assert parameters.command == ['sleep', '50']


def test_run_via_api():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
        docker_run_builder = DockerRunBuilder(additional_opts=['-l', 'hello=there', '-l', 'oh=noo',
                                                               '--name', 'test', '-d',
                                                               '--hostname', 'my_hostname',
                                                               '--rm',
                                                               '--memory', '1G',
                                                               '--workdir', '/tmp',
                                                               '--env', 'ENV1=my_env', '-p', '123:12345',
                                                               '--cap-add', 'MKNOD', '--cap-add', 'SYS_ADMIN',
                                                               '--cap-drop', 'SYS_ADMIN',
                                                               '--dns', 'www.example.com',
                                                               '--volume', '/tmp:/tmp', '--no-healthcheck'],
                                              command=['sleep', '10'])

        parameters = docker_run_builder.get_parameters()

        c = image.run_via_api(parameters)

        try:
            assert "Config" in c.inspect()
            assert c.get_id() == str(c)
            assert repr(c)
            assert isinstance(c.get_id(), string_types)
        finally:
            c.delete(force=True)

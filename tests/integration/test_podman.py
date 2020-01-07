from __future__ import print_function, unicode_literals

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG, \
    FEDORA_REPOSITORY, FEDORA_MINIMAL_IMAGE_REGEX, FEDORA_MINIMAL_NAME_REGEX

import subprocess
import time

from conu.backend.podman.container import PodmanRunBuilder
from conu.backend.podman.image import PodmanImagePullPolicy
from conu.utils import check_podman_command_works, are_we_root
from conu.utils.probes import Probe
from conu.fixtures import podman_backend
from conu.apidefs.metadata import ContainerStatus
from conu.exceptions import ConuException
from conu import Directory

from six import string_types

import pytest
import re


@pytest.fixture()
def podman_run_builder():
    prb = PodmanRunBuilder()
    # there is no journal in a container:
    #   ERRO[0001] unable to write pod event:
    #   "write unixgram @00120->/run/systemd/journal/socket:
    #     sendmsg: no such file or directory"
    # prb.global_options = ["--events-backend=none"]
    # alternatively, do this in /etc/containers/libpod.conf
    return prb


def test_podman_cli():
    """
    Test if podman CLI works
    """
    assert check_podman_command_works()


def test_podman_version(podman_backend):
    assert podman_backend.get_version() is not None


def test_podman_image(podman_backend):
    """
    Test interaction with an image
    """
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    assert "%s:%s" % (FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG) == image.get_full_name()
    assert "%s:%s" % (FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG) in image.inspect()['RepoTags']
    assert "Config" in image.inspect()
    assert re.match(FEDORA_MINIMAL_NAME_REGEX, image.get_full_name())
    assert re.match(FEDORA_MINIMAL_IMAGE_REGEX, str(image))
    assert "PodmanImage(repository=%s, tag=%s)" % (FEDORA_MINIMAL_REPOSITORY,
                                                   FEDORA_MINIMAL_REPOSITORY_TAG) == repr(image)
    assert isinstance(image.get_id(), string_types)
    new_image = image.tag_image(tag="test")
    assert new_image.is_present()
    new_image.rmi(via_name=True)
    assert not new_image.is_present()


def test_image_wrong_types(podman_backend):
    with pytest.raises(ConuException) as exc:
        podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, PodmanImagePullPolicy.NEVER)
        assert "tag" in exc.value.message


def test_container(podman_backend, podman_run_builder):
    """
    Basic tests of interacting with a podman container
    """
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    podman_run_builder.arguments += ["cat"]
    podman_run_builder.options += ["-i", "-t"]
    c = image.run_via_binary(run_command_instance=podman_run_builder)
    try:
        assert c.is_running()
        assert "Config" in c.inspect()
        assert "Config" in c.inspect()
        assert c.get_id() == str(c)
        assert repr(c)
        assert isinstance(c.get_id(), string_types)
    finally:
        c.delete(force=True)


def test_container_create_failed(podman_backend, podman_run_builder):
    """
    Test podman run with execution non-existing command
    """
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    podman_run_builder.arguments += ["waldo"]
    # should raise an exc, there is no such command: waldo; we need to find waldo first
    with pytest.raises(ConuException):
        image.run_via_binary(run_command_instance=podman_run_builder)
    # podman is not deterministic here: sometimes it fails to create the container saying
    # waldo is not inside, and sometimes the container gets created
    # and then start produces a very wierd error message:
    #   "error reading container (probably exited) json message: EOF"
    # container = image.run_via_binary_in_foreground(run_command_instance=podman_run_builder)
    # assert not container.is_running()
    # container.start()


def test_interactive_container(podman_backend, podman_run_builder):
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    podman_run_builder.arguments = ["bash"]
    podman_run_builder.options += ["-i"]
    cont = image.run_via_binary_in_foreground(
        run_command_instance=podman_run_builder,
        popen_params={"stdin": subprocess.PIPE, "stdout": subprocess.PIPE}
    )
    try:
        assert cont.is_running()
        assert "" == cont.logs()
        assert cont.is_running()
        time.sleep(0.1)
        cont.popen_instance.stdin.write(b"echo palacinky\n")
        cont.popen_instance.stdin.flush()
        time.sleep(0.2)
        assert b"palacinky" in cont.popen_instance.stdout.readline()
    finally:
        cont.delete(force=True)


def test_container_logs(podman_backend, podman_run_builder):
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    podman_run_builder.arguments = ["bash", "-c", "for x in `seq 1 5`; do echo $x; done"]
    cont = image.run_via_binary(run_command_instance=podman_run_builder)
    try:
        Probe(timeout=5, fnc=cont.is_running, expected_retval=False).run()
        assert not cont.is_running()
        assert list(cont.logs()) == ['1', '\n', '2', '\n', '3', '\n', '4', '\n', '5', '\n']
    finally:
        cont.delete(force=True)


@pytest.mark.skipif(not are_we_root(),
                    reason="rootless containers don't provide networking metadata, yet")
def test_http_client(podman_backend, podman_run_builder):
    image = podman_backend.ImageClass(FEDORA_REPOSITORY)
    podman_run_builder.arguments = ["python3", "-m", "http.server", "--bind", "0.0.0.0", "8000"]
    c = image.run_via_binary(run_command_instance=podman_run_builder)
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


@pytest.mark.skipif(not are_we_root(),
                    reason="rootless containers don't provide networking metadata, yet")
def test_http_client_context(podman_backend, podman_run_builder):
    image = podman_backend.ImageClass(FEDORA_REPOSITORY)
    podman_run_builder.arguments = ["python3", "-m", "http.server", "--bind", "0.0.0.0", "8000"]
    c = image.run_via_binary(run_command_instance=podman_run_builder)
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


def test_wait_for_status(podman_backend):
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = ['true']
    cont = image.run_via_binary(command=cmd)

    try:
        p = Probe(timeout=6, fnc=cont.is_running, expected_retval=False)
        p.run()  # let's wait for the container to exit
        assert cont.exit_code() == 0  # let's make sure it exited fine
    finally:
        cont.delete(force=True)


def test_exit_code(podman_backend):
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    cmd = ['sleep', '0.3']
    cont = image.run_via_binary(command=cmd)
    try:
        p = Probe(timeout=5, fnc=cont.is_running, expected_retval=False)
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


def test_execute(podman_backend, podman_run_builder):
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    podman_run_builder.arguments = ['sleep', 'infinity']
    cont = image.run_via_binary(run_command_instance=podman_run_builder)
    cont.execute(["bash", "-c", "exit 0"])
    assert "asd\nasd" == cont.execute(["printf", "asd\nasd"])
    assert "asd" == cont.execute(["printf", "asd"])
    with pytest.raises(subprocess.CalledProcessError) as ex:
        cont.execute(["bash", "-c", "exit 110"])
        assert "exit code 110" in ex.value.message
        assert "bash" in ex.value.message


def test_pull_always(podman_backend):
    image = podman_backend.ImageClass("docker.io/library/busybox", tag="latest",
                                      pull_policy=PodmanImagePullPolicy.ALWAYS)
    try:
        assert image.is_present()
    finally:
        image.rmi(force=True)


def test_pull_if_not_present(podman_backend):
    image = podman_backend.ImageClass("docker.io/library/busybox", tag="1.29.3")
    try:
        assert image.is_present()
    finally:
        image.rmi(force=True)


def test_pull_never(podman_backend):
    with pytest.raises(subprocess.CalledProcessError):
        podman_backend.ImageClass._inspect("busybox:1.25.1")
    image = podman_backend.ImageClass("docker.io/library/busybox", tag="1.29.3",
                               pull_policy=PodmanImagePullPolicy.NEVER)
    assert not image.is_present()


def test_set_name(podman_backend):
    test_name = 'jondoe'
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                      pull_policy=PodmanImagePullPolicy.NEVER)
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


def test_run_with_volumes_metadata_check(tmpdir, podman_backend):
    t = str(tmpdir)
    mountpoint_path = "/mountpoint"
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                                      pull_policy=PodmanImagePullPolicy.NEVER)
    container = image.run_via_binary(volumes=(Directory(t), mountpoint_path, "Z"))
    try:
        for mount in container.inspect()["Mounts"]:
            source = mount.get("source", mount["Source"])
            dest = mount.get("destination", mount["Destination"])
            options = mount.get("options", mount["Options"])
            if source == t and dest == mountpoint_path:
                # :Z is no longer present in the options
                break
        # break was not reached: the mountpoint was not found
        else:
            assert False, "No mountpoint matching criteria: %s:%s:%s" % (t, mountpoint_path, "Z")
    finally:
        container.delete(force=True)


def test_list_containers(podman_backend):
    l = len(podman_backend.list_containers())
    assert l >= 0
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG,
                               pull_policy=PodmanImagePullPolicy.NEVER)
    prb = PodmanRunBuilder(command=["sleep", "1"], additional_opts=[
        "-e", "FOO=BAR",
    ])
    container = image.run_via_binary(run_command_instance=prb)
    try:
        container_list = podman_backend.list_containers()
        l = len(container_list)
        assert l >= 1
        print(container_list[0].metadata.identifier)
        cont_under_test = [x for x in container_list
                           if x.metadata.identifier == container.get_id()][0]
        assert cont_under_test.metadata.image
        assert cont_under_test.metadata.command
        assert cont_under_test.metadata.env_variables["FOO"] == "BAR"
        assert cont_under_test.get_IPv4s()
    finally:
        container.delete(force=True)


def test_list_images(podman_backend):
    image_list = podman_backend.list_images()
    assert len(image_list) > 0
    # id of registry.fedoraproject.org/fedora-minimal:31
    the_id = subprocess.check_output(["podman", "inspect", "-f", "{{.Id}}",
                                      FEDORA_MINIMAL_REPOSITORY + ":" +
                                      FEDORA_MINIMAL_REPOSITORY_TAG]).decode("utf-8").strip()
    images = {image.get_id(): image for image in image_list}
    assert the_id in images
    image = images[the_id]
    assert image.metadata.digest
    assert image.metadata.repo_digests


def test_container_metadata(podman_backend):
    image = podman_backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)
    # TODO: add port bindings to the mix once they are supported in rootless mode
    c = image.run_via_binary(
        PodmanRunBuilder(command=["cat"], additional_opts=['-i',
                                                           '-t',
                                                           '--name', 'mycontainer',
                                                           # '-p', '1234:12345',
                                                           # '-p', '123:12345',
                                                           # '-p', '8080',
                                                           '--hostname', 'my_hostname',
                                                           '-e', 'ENV1=my_env',
                                                           '-e', 'ASD=',
                                                           '-e', 'A=B=C=D',
                                                           '--label', 'testlabel1=testvalue1'
                                                           ])
    )

    try:
        container_metadata = c.get_metadata()

        assert container_metadata.command == ["cat"]
        assert container_metadata.name == "mycontainer"
        assert container_metadata.env_variables["ENV1"] == "my_env"
        assert container_metadata.env_variables["ASD"] == ""
        assert container_metadata.env_variables["A"] == "B=C=D"
        assert container_metadata.hostname == "my_hostname"

        # FIXME: podman raise an error when you send option  '-e XYZ': no such env variable
        # assert "XYZ" not in list(container_metadata.env_variables.keys())
        # assert 12345 in container_metadata.port_mappings
        # assert container_metadata.port_mappings[12345] == [1234, 123]
        # assert 8080 in container_metadata.port_mappings
        # assert set(container_metadata.exposed_ports) == {8080, 12345}
        assert container_metadata.labels["testlabel1"] == "testvalue1"
        assert container_metadata.status == ContainerStatus.RUNNING
    finally:
        c.delete(force=True)

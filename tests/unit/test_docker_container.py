from __future__ import print_function, unicode_literals

from conu import DockerRunBuilder, DockerImage


def test_dr_command_class():
    simple = DockerRunBuilder()
    simple.image_name = "voodoo"
    assert ["docker", "container", "run", "voodoo"] == simple.build()

    complex = DockerRunBuilder(additional_opts=["-a", "--foo"])
    complex.image_name = "voodoo"
    assert ["docker", "container", "run", "-a", "--foo", "voodoo"] == complex.build()

    w_cmd = DockerRunBuilder(command=["x", "y"], additional_opts=["-a", "--foo"])
    w_cmd.image_name = "voodoo"
    assert ["docker", "container", "run", "-a", "--foo", "voodoo", "x", "y"] == w_cmd.build()

    # test whether mutable params are not mutable across instances
    simple.options += ["spy"]
    assert "spy" not in DockerRunBuilder().options


def test_get_port_mappings():
    image_name = "registry.fedoraproject.org/fedora"
    image_tag = "27"
    image = DockerImage(image_name, image_tag)

    command = DockerRunBuilder(additional_opts=["-p", "321:123"])

    try:
        image.get_metadata()
    except Exception:
        image.pull()

    container = image.run_via_binary(command)
    try:
        mappings = container.get_port_mappings(123)

        assert len(mappings) == 1
        assert mappings == [{"HostIp": '0.0.0.0', "HostPort": '321'}]

        mappings = container.get_port_mappings()
        assert len(mappings) == 1
        assert mappings == {'123/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '321'}]}
    finally:
        container.stop()
        container.delete()

    command = DockerRunBuilder()
    container = image.run_via_binary(command)
    try:
        mappings = container.get_port_mappings(123)

        assert not mappings
    finally:
        container.stop()
        container.delete()

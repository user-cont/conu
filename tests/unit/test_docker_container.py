from __future__ import print_function, unicode_literals

from conu import DockerRunCommand


def test_dr_command_class():
    simple = DockerRunCommand()
    simple.image_name = "voodoo"
    assert ["docker", "container", "run", "voodoo"] == simple.build()

    complex = DockerRunCommand(additional_opts=["-a", "--foo"])
    complex.image_name = "voodoo"
    assert ["docker", "container", "run", "-a", "--foo", "voodoo"] == complex.build()

    w_cmd = DockerRunCommand(command=["x", "y"], additional_opts=["-a", "--foo"])
    w_cmd.image_name = "voodoo"
    assert ["docker", "container", "run", "-a", "--foo", "voodoo", "x", "y"] == w_cmd.build()

    # test whether mutable params are not mutable across instances
    simple.options += ["spy"]
    assert "spy" not in DockerRunCommand().options

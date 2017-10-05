from __future__ import print_function, unicode_literals

import subprocess

from conu.utils.core import Volume, Probe, run_cmd


def test_volume():
    vol1 = Volume()
    vol1.clean()
    vol2 = Volume()
    assert "/tmp" in str(vol2)
    vol2.clean()

    vol3 = Volume(directory="/tmp/superdir", target="/tmp", permissions="a+x")
    assert "/tmp/superdir" == str(vol3)
    assert "-v /tmp/superdir:/tmp" == vol3.docker()
    vol3.set_force_selinux(True)
    vol3.set_facl(["u:26:rwx"])
    assert "-v /tmp/superdir:/tmp:Z" == vol3.docker()
    vol3.clean()


def test_probes_port():
    p1 = Probe()
    port = 1234
    host = "127.0.0.1"

    assert not p1.check_port(host=host, port=port)

    bckgrnd = run_cmd(["nc", "-l", str(port)], raw=True, stdout=subprocess.PIPE)
    assert p1.wait_inet_port(host, port, count=10)
    assert not p1.check_port(host=host, port=port)
    bckgrnd.kill()
    assert not p1.check_port(host=host, port=port)

    bckgrnd = run_cmd(["nc", "-l", str(port)], raw=True, stdout=subprocess.PIPE)
    assert p1.wait_inet_port(host, port, count=10)
    assert not p1.check_port(host=host, port=port)


if __name__ == "__main__":
    test_volume()
    test_probes_port()

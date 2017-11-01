from __future__ import print_function, unicode_literals

import subprocess

from conu.utils.core import Volume, run_cmd, check_port
from conu.utils.probes import Probe


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
    port = 1234
    host = "127.0.0.1"
    probe = Probe(timeout=20, fnc=check_port, host=host, port=port)
    assert not check_port(host=host, port=port)

    bckgrnd = run_cmd(["nc", "-l", str(port)], raw=True, stdout=subprocess.PIPE)
    assert probe.run()
    assert not check_port(host=host, port=port)
    bckgrnd.kill()
    assert not check_port(host=host, port=port)

    bckgrnd = run_cmd(["nc", "-l", str(port)], raw=True, stdout=subprocess.PIPE)
    assert probe.run()
    assert not check_port(host=host, port=port)


if __name__ == "__main__":
    test_volume()
    test_probes_port()

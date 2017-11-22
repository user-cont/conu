# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import subprocess

from conu import check_port, Probe


def test_probes_port():
    port = 1234
    host = "127.0.0.1"
    probe = Probe(timeout=20, fnc=check_port, host=host, port=port)
    assert not check_port(host=host, port=port)

    bckgrnd = subprocess.Popen(["nc", "-l", str(port)], stdout=subprocess.PIPE)
    assert probe.run()
    assert not check_port(host=host, port=port)
    bckgrnd.kill()
    assert not check_port(host=host, port=port)

    subprocess.Popen(["nc", "-l", str(port)], stdout=subprocess.PIPE)
    assert probe.run()
    assert not check_port(host=host, port=port)

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

import subprocess

import pytest

from conu import check_port, Probe
from conu.utils import s2i_command_exists, getenforce_command_exists, \
    chcon_command_exists, setfacl_command_exists, command_exists, CommandDoesNotExistException, \
    check_docker_command_works


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


def test_required_binaries_exist():
    # should work since we have all the deps installed
    assert s2i_command_exists()
    assert getenforce_command_exists()
    assert chcon_command_exists()
    assert setfacl_command_exists()


def test_command_exists():
    m = "msg"
    command_exists("printf", ["printf", "--version"], m)
    with pytest.raises(CommandDoesNotExistException) as exc:
        command_exists("printof", ["printof", "--versionotron"], m)
        assert exc.value.msg == m


def test_check_docker():
    assert check_docker_command_works()

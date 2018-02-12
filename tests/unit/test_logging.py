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
"""
Unit tests for logging system in conu

TODO:
* seems like {cap,catch}log is going to be part of pytest core:
    https://github.com/pytest-dev/pytest/pull/2794
"""
from __future__ import print_function, unicode_literals

import logging

from conu.apidefs.backend import Backend


def test_capturing(caplog):
    Backend()
    # backend.py                  52 INFO     conu has initiated, welcome to the party!
    for r in caplog.records:
        assert r.name == "conu"
        assert r.module == "backend"
        assert r.msg == "conu has initiated, welcome to the party!"
        assert r.levelno == 20


def test_level_setting(caplog):
    Backend(logging_level=logging.DEBUG)
    r = caplog.records[1]
    # backend.py                  53 DEBUG    conu version: 0.0.1-alpha
    assert r.name == "conu"
    assert r.module == "backend"
    assert r.msg == "conu version: %s"
    assert r.levelno == 10

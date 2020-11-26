# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
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


def test_logger_has_single_handler():
    logger = logging.getLogger('conu')
    assert len(logger.handlers) == 1

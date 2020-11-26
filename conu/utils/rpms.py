# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

import re
import logging

from conu.exceptions import PackageSignatureException

NONE_KEY = '(none)'
KEY = r'.*Key ID ([a-h0-9]+)'
no_key_pkgs = ['gpg-pubkey']

logger = logging.getLogger(__name__)


def process_rpm_ql_line(line_str, allowed_keys):
    """
    Checks single line of rpm-ql for correct keys

    :param line_str: line to process
    :param allowed_keys: list of allowed keys
    :return: bool
    """
    try:
        name, key_str = line_str.split(' ', 1)
    except ValueError:
        logger.error("Failed to split line '{0}".format(repr(line_str)))
        return False
    if name in no_key_pkgs:
        return True
    if key_str == NONE_KEY:
        logger.error("Unsigned package {0}".format(name))
        return False
    key_match = re.match(KEY, key_str)
    if not key_match:
        logger.error('Could not process line "{0}"'.format(line_str))
        return False
    used_key = key_match.group(1)
    if used_key in allowed_keys:
        return True
    logger.error("Wrong key for '{0}' ({1})".format(name, used_key))
    return False


def check_signatures(pkg_list, allowed_keys):
    """
    Go through list of packages with signatures and check if all are properly signed

    :param pkg_list: list of packages in format '%{name} %{SIGPGP:pgpsig}'
    :param allowed_keys: list of allowed keys
    :return: bool
    """
    all_passed = True
    for line_str in pkg_list:
        all_passed &= process_rpm_ql_line(line_str.strip(), allowed_keys)

    if not all_passed:
        raise PackageSignatureException(
            'Error while checking rpm signatures, see logs for more info')

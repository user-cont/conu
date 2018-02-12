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

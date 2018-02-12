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
singleton instance of docker.APIClient
"""
from __future__ import print_function, unicode_literals

from conu.utils import check_docker_command_works

import docker


client = None


def get_client():
    global client
    if client is None:
        # FIXME: once we implement `run_via_api`, move this elsewhere; ideally to run_via_binary
        #        and check only once
        check_docker_command_works()
        try:
            client = docker.APIClient(version="auto")  # >= 2
        except AttributeError:
            client = docker.Client(version="auto")  # < 2
    return client

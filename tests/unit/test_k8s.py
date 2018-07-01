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
Tests for Kubernetes backend
"""

from conu.backend.k8s.utils import k8s_ports_to_metadata_ports, metadata_ports_to_k8s_ports


def test_port_conversion():
    test_ports = ["8080/tcp", "12345"]

    k8s_ports = metadata_ports_to_k8s_ports(test_ports)

    assert test_ports == k8s_ports_to_metadata_ports(k8s_ports)

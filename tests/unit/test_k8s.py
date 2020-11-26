# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

"""
Tests for Kubernetes backend
"""

from conu.backend.k8s.utils import k8s_ports_to_metadata_ports, metadata_ports_to_k8s_ports


def test_port_conversion():
    test_ports = ["8080/tcp", "12345"]

    k8s_ports = metadata_ports_to_k8s_ports(test_ports)

    assert test_ports == k8s_ports_to_metadata_ports(k8s_ports)

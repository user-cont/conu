# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

"""
utility functions related to kubernetes
"""
from kubernetes import client


def k8s_ports_to_metadata_ports(k8s_ports):
    """
    :param k8s_ports: list of V1ServicePort
    :return: list of str, list of exposed ports, example:
            - ['1234/tcp', '8080/udp']
    """

    ports = []

    for k8s_port in k8s_ports:
        if k8s_port.protocol is not None:
            ports.append("%s/%s" % (k8s_port.port, k8s_port.protocol.lower()))
        else:
            ports.append(str(k8s_port.port))

    return ports


def metadata_ports_to_k8s_ports(ports):
    """
    :param ports: list of str, list of exposed ports, example:
            - ['1234/tcp', '8080/udp']
    :return: list of V1ServicePort
    """

    exposed_ports = []

    for port in ports:
        splits = port.split("/", 1)
        port = int(splits[0])
        protocol = splits[1].upper() if len(splits) > 1 else None
        exposed_ports.append(client.V1ServicePort(port=port, protocol=protocol))

    return exposed_ports

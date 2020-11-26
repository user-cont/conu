# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

"""
singleton instances of kubernetes client
"""

from kubernetes import client, config


core_api = None
apps_api = None

API_KEY = None


def get_core_api():
    """
    Create instance of Core V1 API of kubernetes:
    https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CoreV1Api.md
    :return: instance of client
    """
    global core_api

    if core_api is None:
        config.load_kube_config()
        if API_KEY is not None:
            # Configure API key authorization: BearerToken
            configuration = client.Configuration()
            configuration.api_key['authorization'] = API_KEY
            configuration.api_key_prefix['authorization'] = 'Bearer'
            core_api = client.CoreV1Api(client.ApiClient(configuration))
        else:
            core_api = client.CoreV1Api()

    return core_api


def get_apps_api():
    """
    Create instance of Apps V1 API of kubernetes:
    https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/AppsV1Api.md
    :return: instance of client
    """
    global apps_api

    if apps_api is None:
        config.load_kube_config()
        if API_KEY is not None:
            # Configure API key authorization: BearerToken
            configuration = client.Configuration()
            configuration.api_key['authorization'] = API_KEY
            configuration.api_key_prefix['authorization'] = 'Bearer'
            apps_api = client.AppsV1Api(client.ApiClient(configuration))
        else:
            apps_api = client.AppsV1Api()

    return apps_api

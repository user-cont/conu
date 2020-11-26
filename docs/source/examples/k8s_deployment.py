# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

"""
Create deployment using template and check if all pods are ready
"""
import logging

from conu import K8sBackend
from conu.backend.k8s.deployment import Deployment
from conu.utils import get_oc_api_token

# obtain API key from OpenShift cluster. If you are not using OpenShift cluster for kubernetes tests
# you need to replace `get_oc_api_token()` with your Bearer token. More information here:
# https://kubernetes.io/docs/reference/access-authn-authz/authentication/
api_key = get_oc_api_token()

with K8sBackend(api_key=api_key, logging_level=logging.DEBUG) as k8s_backend:

    namespace = k8s_backend.create_namespace()

    template = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hello-world
      labels:
        app: hello-world
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: hello-world
      template:
        metadata:
          labels:
            app: hello-world
        spec:
          containers:
          - name: hello-openshift
            image: openshift/hello-openshift
    """

    test_deployment = Deployment(namespace=namespace, from_template=template,
                                 create_in_cluster=True)

    try:
        test_deployment.wait(200)
        assert test_deployment.all_pods_ready()
    finally:
        test_deployment.delete()
        k8s_backend.delete_namespace(namespace)

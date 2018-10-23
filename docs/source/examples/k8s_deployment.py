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

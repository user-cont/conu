# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

import logging

from conu import K8sBackend, \
                 DockerBackend
from conu.backend.k8s.pod import PodPhase
from conu.utils import get_oc_api_token

api_key = get_oc_api_token()
with K8sBackend(api_key=api_key, logging_level=logging.DEBUG) as k8s_backend:

    namespace = k8s_backend.create_namespace()

    with DockerBackend(logging_level=logging.DEBUG) as backend:
        image = backend.ImageClass("openshift/hello-openshift")

        pod = image.run_in_pod(namespace=namespace)

        try:
            pod.wait(200)
            assert pod.is_ready()
            assert pod.get_phase() == PodPhase.RUNNING
        finally:
            pod.delete()
            assert pod.get_phase() == PodPhase.TERMINATING
            k8s_backend.delete_namespace(namespace)

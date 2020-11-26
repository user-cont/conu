# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

import logging

from conu import OpenshiftBackend, \
                 DockerBackend
from conu.backend.origin.registry import login_to_registry
from conu.utils import get_oc_api_token

api_key = get_oc_api_token()
with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

    openshift_backend.get_status()

    python_image = openshift_backend.import_image("python-36-centos7",
                                                  "docker.io/centos/python-36-centos7")

    # create new app from local source in OpenShift cluster
    app_name = openshift_backend.create_new_app_from_source(
        python_image,
        source="examples/openshift/standalone-test-app",
        project='myproject')

    try:
        # wait until service is ready to accept requests
        openshift_backend.wait_for_service(
            app_name=app_name,
            port=8080,
            expected_output="Hello World from standalone WSGI application!")
    finally:
        openshift_backend.get_logs(app_name)
        openshift_backend.clean_project(app_name)

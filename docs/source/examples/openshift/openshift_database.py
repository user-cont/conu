# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

import logging

from conu import OpenshiftBackend
from conu.utils import get_oc_api_token

api_key = get_oc_api_token()
with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

    openshift_backend.get_status()

    mariadb_image = openshift_backend.import_image("mariadb-102-centos7",
                                                   "centos/mariadb-102-centos7")

    app_name = openshift_backend.create_new_app_from_source(
        mariadb_image,
        oc_new_app_args=[
            "--env", "MYSQL_ROOT_PASSWORD=test",
            "--env", "MYSQL_OPERATIONS_USER=test1",
            "--env", "MYSQL_OPERATIONS_PASSWORD=test1",
            "--env", "MYSQL_DATABASE=testdb",
            "--env", "MYSQL_USER=user1",
            "--env", "MYSQL_PASSWORD=user1"],
        source="examples/openshift/extend-mariadb-image",
        project='myproject')

    openshift_backend.get_status()

    try:
        openshift_backend.wait_for_service(
            app_name=app_name,
            port=3306,
            timeout=300)
        assert openshift_backend.all_pods_are_ready(app_name)
    finally:
        openshift_backend.get_logs(app_name)
        openshift_backend.clean_project(app_name)

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

    openshift_backend.create_app_from_template(
        image_name="centos/python-36-centos7",
        name="django-psql-example",
        template="https://raw.githubusercontent.com/sclorg/django-ex"
                 "/master/openshift/templates/django-postgresql.json",
        oc_new_app_args=["-p", "NAMESPACE=%s" % "myproject",
                         "-p", "NAME=%s" % "django-psql-example",
                         "-p", "SOURCE_REPOSITORY_REF=master", "-p",
                         "PYTHON_VERSION=3.6",
                         "-p", "POSTGRESQL_VERSION=%s" % "9.6"],
        name_in_template={"python": "3.6"},
        other_images=[{"%s:%s" % ("centos/postgresql-96-centos7", "9.6"):
                           "postgresql:%s" % "9.6"}],
        project="myproject")

    try:
        openshift_backend.wait_for_service(
            app_name="django-psql-example",
            port=8080,
            expected_output='Welcome to your Django application on OpenShift',
            timeout=300)
    finally:
        openshift_backend.get_logs("django-psql-example")
        # pass name from template as argument
        openshift_backend.clean_project("django-psql-example")

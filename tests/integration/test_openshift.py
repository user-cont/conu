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
Tests for OpenShift backend
"""

import logging
import pytest

from conu import OpenshiftBackend
from conu.utils import get_oc_api_token, oc_command_exists, is_oc_cluster_running
from ..constants import CENTOS_MARIADB_10_2, CENTOS_PYTHON_3, MY_PROJECT,\
    CENTOS_POSTGRES_9_6, CENTOS_POSTGRES_9_6_TAG, DJANGO_POSTGRES_TEMPLATE, INTERNAL_REGISTRY_URL


@pytest.mark.skipif(not oc_command_exists(), reason="OpenShift is not installed!")
@pytest.mark.skipif(not is_oc_cluster_running(), reason="OpenShift cluster is not running!")
class TestOpenshift(object):

    def test_get_project_name(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:
            assert openshift_backend.get_current_project() == MY_PROJECT

    def test_import_image(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:
            image_name = "mariadb"
            openshift_backend.import_image(image_name, CENTOS_MARIADB_10_2)

            # check if image was successfully imported to internal registry
            assert openshift_backend.get_image_registry_url("mariadb") == INTERNAL_REGISTRY_URL + \
                   "/" + MY_PROJECT + "/" + "mariadb"

    def test_deploy_image(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:
            # create new app from remote source in OpenShift cluster
            app_name = openshift_backend.deploy_image(CENTOS_MARIADB_10_2,
                                                      oc_new_app_args=[
                                                          "--env", "MYSQL_ROOT_PASSWORD=test"],
                                                      project=MY_PROJECT)

            try:
                # wait until service is ready to accept requests
                openshift_backend.wait_for_service(
                    app_name=app_name,
                    port=3306,
                    timeout=300)
                assert openshift_backend.all_pods_are_ready(app_name)
            finally:
                openshift_backend.get_logs(app_name)
                openshift_backend.clean_project(app_name)

    def test_oc_s2i_local_mariadb(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            openshift_backend.get_status()

            app_name = openshift_backend.create_new_app_from_source(
                CENTOS_MARIADB_10_2,
                oc_new_app_args=[
                    "--env", "MYSQL_ROOT_PASSWORD=test",
                    "--env", "MYSQL_OPERATIONS_USER=test1",
                    "--env", "MYSQL_OPERATIONS_PASSWORD=test1",
                    "--env", "MYSQL_DATABASE=testdb",
                    "--env", "MYSQL_USER=user1",
                    "--env", "MYSQL_PASSWORD=user1"],
                source="examples/openshift/extend-mariadb-image",
                project=MY_PROJECT)

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

    def test_oc_s2i_remote(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            openshift_backend.get_status()

            app_name = openshift_backend.create_new_app_from_source(
                CENTOS_PYTHON_3,
                source="https://github.com/openshift/django-ex.git",
                project=MY_PROJECT)

            try:
                openshift_backend.wait_for_service(
                    app_name=app_name,
                    port=8080,
                    expected_output='Welcome to your Django application on OpenShift',
                    timeout=300)
            finally:
                openshift_backend.get_logs(app_name)
                openshift_backend.clean_project(app_name)

    def test_oc_s2i_local(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            openshift_backend.get_status()

            app_name = openshift_backend.create_new_app_from_source(
                CENTOS_PYTHON_3,
                source="examples/openshift/standalone-test-app",
                project=MY_PROJECT)

            try:
                openshift_backend.wait_for_service(
                    app_name=app_name,
                    port=8080,
                    expected_output="Hello World from standalone WSGI application!",
                    timeout=300)
            finally:
                openshift_backend.get_logs(app_name)
                openshift_backend.clean_project(app_name)

    def test_oc_s2i_template(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            openshift_backend.get_status()

            openshift_backend.create_app_from_template(
                image_name=CENTOS_PYTHON_3,
                name=DJANGO_POSTGRES_TEMPLATE,
                template="https://raw.githubusercontent.com/sclorg/django-ex"
                         "/master/openshift/templates/django-postgresql.json",
                oc_new_app_args=["-p", "NAMESPACE=%s" % MY_PROJECT,
                                 "-p", "NAME=%s" % DJANGO_POSTGRES_TEMPLATE,
                                 "-p", "SOURCE_REPOSITORY_REF=master", "-p",
                                 "PYTHON_VERSION=3.6",
                                 "-p", "POSTGRESQL_VERSION=%s" % CENTOS_POSTGRES_9_6_TAG],
                name_in_template={"python": "3.6"},
                other_images=[{"%s:%s" % (CENTOS_POSTGRES_9_6, CENTOS_POSTGRES_9_6_TAG):
                                   "postgresql:%s" % CENTOS_POSTGRES_9_6_TAG}],
                project=MY_PROJECT)

            try:
                openshift_backend.wait_for_service(
                    app_name=DJANGO_POSTGRES_TEMPLATE,
                    port=8080,
                    expected_output='Welcome to your Django application on OpenShift',
                    timeout=300)
            finally:
                openshift_backend.get_logs(DJANGO_POSTGRES_TEMPLATE)
                # pass name from template as argument
                openshift_backend.clean_project(DJANGO_POSTGRES_TEMPLATE)

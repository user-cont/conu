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

from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend
from conu.utils import get_oc_api_token, oc_command_exists, is_oc_cluster_running


@pytest.mark.skipif(not oc_command_exists(), reason="OpenShift is not installed!")
@pytest.mark.skipif(not is_oc_cluster_running(), reason="OpenShift cluster is not running!")
class TestOpenshift(object):

    def test_oc_s2i_remote(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            with DockerBackend(logging_level=logging.DEBUG) as backend:
                python_image = backend.ImageClass("centos/python-36-centos7")

                OpenshiftBackend.login_to_registry('developer')

                app_name = openshift_backend.new_app(
                    python_image,
                    source="https://github.com/openshift/django-ex.git",
                    project='myproject')

                try:
                    openshift_backend.wait_for_service(
                        app_name=app_name,
                        expected_output='Welcome to your Django application on OpenShift',
                        timeout=300)
                finally:
                    openshift_backend.clean_project(app_name)

    def test_oc_s2i_local(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            with DockerBackend(logging_level=logging.DEBUG) as backend:
                python_image = backend.ImageClass("centos/python-36-centos7")

                OpenshiftBackend.login_to_registry('developer')

                app_name = openshift_backend.new_app(
                    python_image,
                    source="examples/openshift/standalone-test-app",
                    project='myproject')

                try:
                    openshift_backend.wait_for_service(
                        app_name=app_name,
                        expected_output="Hello World from standalone WSGI application!",
                        timeout=300)
                finally:
                    openshift_backend.clean_project(app_name)

    def test_oc_s2i_template(self):
        api_key = get_oc_api_token()
        with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

            with DockerBackend(logging_level=logging.DEBUG) as backend:
                python_image = backend.ImageClass("centos/python-36-centos7", tag="latest")
                psql_image = backend.ImageClass("centos/postgresql-96-centos7", tag="9.6")

                OpenshiftBackend.login_to_registry('developer')

                app_name = openshift_backend.new_app(
                    image=python_image,
                    template="https://raw.githubusercontent.com/sclorg/django-ex"
                             "/master/openshift/templates/django-postgresql.json",
                    oc_new_app_args=["-p", "SOURCE_REPOSITORY_REF=master", "-p",
                                     "PYTHON_VERSION=3.6",
                                     "-p", "POSTGRESQL_VERSION=9.6"],
                    name_in_template={"python": "3.6"},
                    other_images=[{psql_image: "postgresql:9.6"}],
                    project='myproject')

                try:
                    openshift_backend.wait_for_service(
                        app_name=app_name,
                        expected_output='Welcome to your Django application on OpenShift',
                        timeout=300)
                finally:
                    # pass name from template as argument
                    openshift_backend.clean_project('django-psql-example')

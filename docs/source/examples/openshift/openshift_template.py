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

import logging

from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend
from conu.utils import get_oc_api_token


api_key = get_oc_api_token()
with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

    with DockerBackend() as backend:
        # images which this template uses
        python_image = backend.ImageClass("centos/python-36-centos7", tag="latest")
        psql_image = backend.ImageClass("centos/postgresql-96-centos7", tag="9.6")

        # docker login inside OpenShift internal registry
        OpenshiftBackend.login_to_registry('developer')

        # create new app from remote source in OpenShift cluster
        app_name = openshift_backend.new_app(
            image=python_image,
            template="https://raw.githubusercontent.com/sclorg/django-ex"
                     "/master/openshift/templates/django-postgresql.json",
            oc_new_app_args=["-p", "SOURCE_REPOSITORY_REF=master", "-p", "PYTHON_VERSION=3.6",
                             "-p", "POSTGRESQL_VERSION=9.6"],
            name_in_template={"python": "3.6"},
            other_images=[{psql_image: "postgresql:9.6"}],
            project='myproject')

        try:
            # wait until service is ready to accept requests
            openshift_backend.wait_for_service(
                app_name=app_name,
                expected_output='Welcome to your Django application on OpenShift',
                timeout=300)
        finally:
            openshift_backend.clean_project(app_name)

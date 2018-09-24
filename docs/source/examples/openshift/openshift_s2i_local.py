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
    with DockerBackend(logging_level=logging.DEBUG) as backend:
        # builder image
        python_image = backend.ImageClass("centos/python-36-centos7")

        # docker login inside OpenShift internal registry
        OpenshiftBackend.login_to_registry('developer')

        # create new app from local source in OpenShift cluster
        app_name = openshift_backend.new_app(python_image,
                                             source="examples/openshift/standalone-test-app",
                                             project='myproject')

        try:
            # wait until service is ready to accept requests
            openshift_backend.wait_for_service(
                app_name=app_name,
                expected_output="Hello World from standalone WSGI application!")
        finally:
            openshift_backend.clean_project(app_name)

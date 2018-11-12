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

from conu import OpenshiftBackend
from conu.utils import get_oc_api_token

api_key = get_oc_api_token()
with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:

    openshift_backend.get_status()

    python_image = openshift_backend.import_image("python-36-centos7",
                                                  "docker.io/centos/python-36-centos7")

    # create new app from remote source in OpenShift cluster
    app_name = openshift_backend.create_new_app_from_source(
        python_image,
        source="https://github.com/openshift/django-ex.git",
        project='myproject')

    try:
        # wait until service is ready to accept requests

        openshift_backend.wait_for_service(
            app_name=app_name,
            port=8080,
            expected_output='Welcome to your Django application on OpenShift',
            timeout=300)
    finally:
        openshift_backend.get_logs(app_name)
        openshift_backend.clean_project(app_name)

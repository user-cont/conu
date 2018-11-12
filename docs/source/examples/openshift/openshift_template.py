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

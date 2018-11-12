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

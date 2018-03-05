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

import subprocess
import logging
import time

from conu import DockerBackend, DockerRunBuilder


environment = ["-e", "POSTGRESQL_USER=user",
               "-e", "POSTGRESQL_PASSWORD=pass",
               "-e", "POSTGRESQL_DATABASE=db"]

with DockerBackend(logging_level=logging.DEBUG) as backend:
    image = backend.ImageClass('centos/postgresql-96-centos7')

    # create server
    additional_opts = environment
    dbcont = image.run_via_binary(additional_opts=additional_opts)

    # wait for server port to be ready
    dbcont.wait_for_port(5432)

    # prepare request
    endpoint = "postgresql://user@" + dbcont.get_IPv4s()[0] + ":5432/" + 'db'
    request_command = DockerRunBuilder(command=['psql', endpoint], additional_opts=['-i'])

    # create client
    clientcont = image.run_via_binary_in_foreground(
        request_command,
        popen_params={"stdin": subprocess.PIPE}
    )

    # send requests
    clientcont.write_to_stdin(b'pass\n')
    # give postgres time to process
    time.sleep(0.1)
    clientcont.write_to_stdin(b'SELECT 1;\n')
    # give postgres time to process
    time.sleep(0.2)
    logs_bytes = clientcont.logs_in_bytes()
    expected_output = b'Password: \n ?column? \n----------\n        1\n(1 row)'
    try:
        assert b'Password: ' in logs_bytes
        assert b'(1 row)' in logs_bytes
        assert clientcont.is_running()
    finally:
        dbcont.delete(force=True)
        clientcont.delete(force=True)

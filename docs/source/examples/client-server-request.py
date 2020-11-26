# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
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

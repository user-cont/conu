import subprocess
import logging
from conu import DockerBackend, DockerRunBuilder

environment = ["-e", "POSTGRESQL_USER=user",
               "-e", "POSTGRESQL_PASSWORD=pass",
               "-e", "POSTGRESQL_DATABASE=db"]

backend = DockerBackend(logging_level=logging.DEBUG)
image = backend.ImageClass('centos/postgresql-96-centos7')

# create server
image.pull()
cmd = DockerRunBuilder(additional_opts=environment)
dbcont = image.run_via_binary(cmd)

# wait for server port to be ready
dbcont.wait_for_port(5432)

# prepare request
endpoint = "postgresql://user@" + dbcont.get_IPv4s()[0] + ":5432/" + 'db'
request_command = DockerRunBuilder(command=['psql', endpoint], additional_opts=['-i'])

# create client
clientcont = image.run_via_binary_in_foreground(request_command, popen_params={"stdin": subprocess.PIPE})
expected_output = b'Password: \n ?column? \n----------\n        1\n(1 row)\n'

# send requests
clientcont.active_write(b'pass\n')
clientcont.active_write(b'SELECT 1;\n')
stdout = clientcont.logs()

try:
    assert stdout == expected_output
    assert clientcont.is_running()
finally:
    dbcont.delete(force=True)
    clientcont.delete(force=True)

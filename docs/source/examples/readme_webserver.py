#!/usr/bin/python3

import logging

from conu import DockerRunBuilder, DockerBackend, random_str, Directory

# our webserver will be accessible on this port
port = 8765

# we'll utilize this container image
image_name = "registry.fedoraproject.org/fedora"
image_tag = "27"

# we'll run our container using docker engine
backend = DockerBackend(logging_level=logging.DEBUG)
image = backend.ImageClass(image_name, tag=image_tag)

# is the image present? if not, pull it
try:
    image.get_metadata()
except Exception:
    image.pull()

# helper class to create `docker run ...` command -- we want to test the same
# experience as our users
b = DockerRunBuilder(
    # the command to run in a container
    command=["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port],
)
# let's run the container (in the background)
container = image.run_via_binary(run_command_instance=b)
try:
    # we need to wait for the webserver to start serving
    container.wait_for_port(port)
    # GET on /
    # this is standard `requests.Response`
    http_response = container.http_request(path="/", port=port)
    assert http_response.ok
    assert '<a href="etc/">etc/</a>' in http_response.content.decode("utf-8")
    # let's access /etc/passwd
    etc_passwd = container.http_request(path="/etc/passwd", port=port).content.decode("utf-8")
    assert 'root:x:0:0:root:/root:' in etc_passwd
    # we can also access it directly on disk and compare
    with container.mount() as fs:
        assert etc_passwd == fs.read_file("/etc/passwd")
finally:
    container.kill()
    container.delete()


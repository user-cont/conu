#!/usr/bin/python3
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

from conu import DockerRunBuilder, DockerBackend

# our webserver will be accessible on this port
port = 8765

# we'll utilize this container image
image_name = "registry.fedoraproject.org/fedora"
image_tag = "27"

# we'll run our container using docker engine
with DockerBackend(logging_level=logging.DEBUG) as backend:
    # the image will be pulled if it's not present
    image = backend.ImageClass(image_name, tag=image_tag)

    # the command to run in a container
    command = ["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port]
    # let's run the container (in the background)
    container = image.run_via_binary(command=command)
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


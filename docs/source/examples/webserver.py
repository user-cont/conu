# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

#!/usr.bin/python3
import logging
import os

from conu import DockerRunBuilder, DockerBackend, random_str, Directory


# this is the port where we can access our app
port = 8765


# convenience function to run our application - webserver
def run_container(backend, local_dir):
    """
    serve path `local_dir` using the python http webserver in a docker container

    :param backend: DockerBackend instance
    :param local_dir: str, path to the directory, it should exist
    :return: instance of DockerContainer
    """
    image_name = "registry.fedoraproject.org/fedora"
    image_tag = "27"

    # we'll run our container using docker engine
    # the image will be pulled if it's not present locally (default behavior)
    image = backend.ImageClass(image_name, tag=image_tag)

    # the command to run in a container
    command = ["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port]
    # additional options passed to `run` command
    additional_opts = ["-w", "/webroot"]

    # let's run the container (in the background)
    container = image.run_via_binary(command=command,
                                     volumes=(local_dir, "/webroot"),
                                     additional_opts=additional_opts)
    return container


def test_webserver():
    # let's setup the directory to serve first
    temp_dir_name = "shiny-%s" % random_str()
    temp_dir_path = os.path.join("/tmp", temp_dir_name)
    with DockerBackend(logging_level=logging.DEBUG) as backend:
        # helper class to create and initialize the dir -- will be removed once we
        # leave the context manager
        with Directory(temp_dir_path, mode=0o0700):
            # let's put some file in it
            with open(os.path.join(temp_dir_path, "candle"), "w") as fd:
                fd.write("You no take candle!")
            container = run_container(backend, temp_dir_path)
            try:
                # we need to wait for the webserver to start serving
                container.wait_for_port(port)
                # GET on /
                http_response = container.http_request(path="/", port=port)
                assert http_response.ok
                assert '<a href="candle">candle</a>' in http_response.content.decode("utf-8")
                # now GETting the file
                assert 'You no take candle!' in container.http_request(
                    path="/candle", port=port).content.decode("utf-8")
            finally:
                container.kill()
                container.delete()


test_webserver()

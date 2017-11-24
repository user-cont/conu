#!/usr.bin/python3
import logging
import os

from conu.backend.docker.container import DockerRunCommand

from conu import DockerBackend
from conu.utils import random_str
from conu.utils.filesystem import Directory


# this is the port where we can access our app
port = 8765


# convenience function to run our application - webserver
def run_container(local_dir):
    """
    serve path `local_dir` using the python http webserver in a docker container
    :param local_dir: str, path to the directory, it should exist
    :return: instance of DockerContainer
    """
    image_name = "registry.fedoraproject.org/fedora"
    image_tag = "27"

    # we'll run our container using docker engine
    backend = DockerBackend(logging_level=logging.DEBUG)
    image = backend.ImageClass(image_name, tag=image_tag)

    # is the image present?
    try:
        image.get_metadata()
    except Exception:
        image.pull()

    # helper class to create `docker run ...` -- we want test the same experience as our users
    b = DockerRunCommand(
        # the command to run in a container
        command=["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port],
        # additional options passed to `run` command
        additional_opts=["-v", "%s:/webroot" % local_dir, "-w", "/webroot"]
    )
    # let's run the container (in the background)
    container = backend.ContainerClass.run_via_binary(image, run_command_instance=b)
    return container


def test_webserver():
    # let's setup the directory to serve first
    temp_dir_name = "shiny-%s" % random_str()
    temp_dir_path = os.path.join("/tmp", temp_dir_name)
    # helper class to create and inittialize the dir -- will be removed once we
    # leave the context manager
    with Directory(temp_dir_path, mode=0o0700):
        # let's put some file in it
        with open(os.path.join(temp_dir_path, "candle"), "w") as fd:
            fd.write("You no take candle!")
        container = run_container(temp_dir_path)
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
            container.rm()


test_webserver()

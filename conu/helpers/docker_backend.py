from conu import DockerRunBuilder


def get_container_output(backend, image_name, command, image_tag="latest",
                         additional_opts=None):
    """
    Create a throw-away container based on provided image and tag, run the supplied command in it
    and return output. The container is stopped and removed after it exits.

    :param backend: instance of DockerBackend
    :param image_name: str, name of the container image
    :param command: list of str, command to run in the container
    :param image_tag: str, container image tag, defaults to "latest"
    :param additional_opts: list of str, by default this function creates the container using
        docker binary and run command; with this argument you can supply addition options to the
        "docker run" invocation
    :return: str (unicode), output of the container
    """
    image = backend.ImageClass(image_name, tag=image_tag)
    # FIXME: use run_via_api and make this a generic function
    c = image.run_via_binary(DockerRunBuilder(command=command, additional_opts=additional_opts))
    try:
        c.wait()
        return c.logs_unicode()
    finally:
        c.stop()
        c.wait()
        c.delete()

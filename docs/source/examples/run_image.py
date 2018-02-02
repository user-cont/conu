from conu import DockerBackend, DockerRunBuilder

with DockerBackend() as backend:
    image = backend.ImageClass('fedora', tag='26')
    command = DockerRunBuilder(command=["ls"], additional_opts=["-i", "-t"])
    container = image.run_via_binary(command)

    container.stop()
    container.delete()

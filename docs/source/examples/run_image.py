from conu import DockerImage, DockerContainer, DockerRunBuilder

image = DockerImage('fedora', tag='26')
image.pull()
command = DockerRunBuilder(command=["ls"], additional_opts=["-i", "-t"])
container = DockerContainer.run_via_binary(image, command)

container.stop()
container.delete()

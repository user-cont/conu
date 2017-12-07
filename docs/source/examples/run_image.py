from conu import DockerImage, DockerRunBuilder

image = DockerImage('fedora', tag='26')
image.pull()
command = DockerRunBuilder(command=["ls"], additional_opts=["-i", "-t"])
container = image.run_via_binary(command)

container.stop()
container.delete()

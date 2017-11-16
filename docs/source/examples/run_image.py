from conu.backend.docker.image import DockerImage
from conu.backend.docker.container import DockerContainer, DockerRunCommand

image = DockerImage('fedora', tag='26')
image.pull()
command = DockerRunCommand(command=["ls"], additional_opts=["-i", "-t"])
container = DockerContainer.run_via_binary(image, command)

container.stop()
container.rm()

from conu.backend.docker.image import DockerImage
from conu.backend.docker.container import DockerContainer, DockerRunCommand

image = DockerImage('centos/httpd-24-centos7')
image.pull()
command = DockerRunCommand(additional_opts=["-p", "8080:8080"])
container = DockerContainer.run_via_binary(image, command)
container.wait_for_port(port=8080, timeout=-1)

container.stop()
container.rm()

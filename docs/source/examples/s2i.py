from conu.backend.docker.image import S2IDockerImage
from conu.backend.docker.container import DockerContainer

source = 'https://github.com/openshift/ruby-hello-world'
image = S2IDockerImage("centos/ruby-23-centos7")
extended_image = image.extend(source, "myapp")
container = DockerContainer.run_via_binary(extended_image)

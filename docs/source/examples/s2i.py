from conu import S2IDockerImage, DockerContainer

source = 'https://github.com/dbarnett/python-helloworld'
image = S2IDockerImage("centos/python-35-centos7")
image.pull()
extended_image = image.extend(source, "myapp")
container = DockerContainer.run_via_binary(extended_image)

container.stop()
container.rm()

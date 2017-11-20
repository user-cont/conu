# conu

`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

# Installation

You can try out conu in your local machine by running:

```commandline
git clone https://github.com/fedora-modularity/conu
sh -c conu/requirements.sh
pip3 install --user ./conu
```

More info [here](http://conu.readthedocs.io/en/latest/installation.html).

# List of features
## Image
- load, pull, mount and remove
- get low-level image information in form of dictionary
- check presence of files and directories in image
- read files in image
- get selinux context of files in image
- extend image using s2i

## Container
- kill, logs, exec, mount, remove, start, stop, wait, run - via api, or via binary
- get low-level container information in form of dictionary
- shortcut methods for getting:
    - IPv4 and IPv6 address
    - PID of root process in container
    - port mappings
    - container status
- HTTP requests support
- open TCP connection
- checks
    - if running
    - mapped port opened

## Utilities
- create and delete testing directory on host with possibility to set attributes:
    - path
    - mode
    - ownership
    - selinux context
    - access control list (facl)
- port availability check
- check selinux status of host
- run a command on host
- easy random string generation
- probe

# Docker example

```python
# TODO: use more complex example with assertions and stuff
from conu.backend.docker.image import DockerImage
from conu.backend.docker.container import DockerContainer, DockerRunCommand

# initialization
image = DockerImage('fedora', tag='26')
image.pull()
command = DockerRunCommand(command=["ls"], additional_opts=["-i", "-t"])
container = DockerContainer.run_via_binary(image, command)

# cleanup
container.stop()
container.rm()
```

# Documentation
For more info see our documentation at [readthedocs.io](http://conu.readthedocs.io/en/latest/).

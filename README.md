# conu

`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

# Installation

## PyPI

`conu` is available on PyPI, so you can easily install it with pip:

```
$ pip install --user conu
```

## Fedora

If you are running Fedora, we have packaged `conu` in an RPM:

```
$ dnf copr enable ttomecek/conu
$ dnf install python{2,3}-conu conu-doc
```

Please visit [our documentation](http://conu.readthedocs.io/en/latest/installation.html) for more info on installation.


# Features

## Container images
- load, pull, mount and remove container images
- obtain low-level image metadata
- check presence of files and directories inside a container image
- read files inside an image
- get selinux context of files in an image
- extend image using [s2i](https://github.com/openshift/source-to-image)

## Container
- kill, get logs, exec a command, mount, remove, start, stop, wait, run - via api or via binary
- get low-level container metadata
- shortcut methods for getting:
    - IPv4 and IPv6 addresses
    - PID of root process in the container
    - port mappings
    - container status
- HTTP requests support
- open a TCP connection with the service inside container
- perform checks whether
    - the container is running
    - mapped ports are opened

## Utilities
- easily create and delete a directory and set its options:
    - mode
    - ownership
    - selinux context
    - access control lists (facl)
- port availability check
- check SELinux status on host
- run a command on host
- easy random string generation
- support for probes (execute a function in a separate process):
    - repeat until a condition is met
    - repeat N times
    - delay execution
    - delay between iterations


# Docker example

Let's look at a practical example:

```bash
$ cat ./example.py
```
```python
import logging

from conu import DockerRunBuilder, DockerBackend, random_str, Directory

# our webserver will be accessible on this port
port = 8765

# we'll utilize this container image
image_name = "registry.fedoraproject.org/fedora"
image_tag = "27"

# we'll run our container using docker engine
backend = DockerBackend(logging_level=logging.DEBUG)
image = backend.ImageClass(image_name, tag=image_tag)

# is the image present? if not, pull it
try:
    image.get_metadata()
except Exception:
    image.pull()

# helper class to create `docker run ...` command -- we want to test the same
# experience as our users
b = DockerRunBuilder(
    # the command to run in a container
    command=["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port],
)
# let's run the container (in the background)
container = image.run_via_binary(run_command_instance=b)
try:
    # we need to wait for the webserver to start serving
    container.wait_for_port(port)
    # GET on /
    # this is standard `requests.Response`
    http_response = container.http_request(path="/", port=port)
    assert http_response.ok
    assert '<a href="etc/">etc/</a>' in http_response.content.decode("utf-8")
    # let's access /etc/passwd
    etc_passwd = container.http_request(path="/etc/passwd", port=port).content.decode("utf-8")
    assert 'root:x:0:0:root:/root:' in etc_passwd
    # we can also access it directly on disk and compare
    with container.mount() as fs:
        assert etc_passwd == fs.read_file("/etc/passwd")
finally:
    container.kill()
    container.delete()
```

Let's run it! Please make sure that you run the provided example as root, since
`conu` utilizes [`atomic`](https://github.com/projectatomic/atomic) tool and its `mount` command, which requires you to
be root.

Let's run it and look at the logs:
```bash
$ python3 ./example.py
```
```
13:55:19.510 backend.py        INFO   conu has initiated, welcome to the party!
13:55:19.510 backend.py        DEBUG  conu version: 0.1.0
13:55:19.520 container.py      INFO   run container via binary in background
13:55:19.875 probes.py         DEBUG  starting probe
13:55:19.877 probes.py         DEBUG  first process started: pid=434
13:55:19.879 probes.py         DEBUG  pausing for 1 before next try
13:55:19.879 probes.py         DEBUG  Running "functools.partial(<bound method DockerContainer.is_port_open of DockerContainer(image=registry.fedoraproject.org/fedora:27, id=4931a079dbf3d52f39f5a530f5bc0025130146b7463f2543f2d8bce5379bd106)>, 8765)" with parameters: "{}":       0/10
13:55:19.886 __init__.py       INFO   trying to open connection to 172.17.0.2:8765
13:55:19.887 __init__.py       INFO   was connection successful? errno: 111
13:55:19.887 __init__.py       DEBUG  port is closed: 172.17.0.2:8765
13:55:20.881 probes.py         INFO   waiting for process to end...
13:55:20.881 probes.py         DEBUG  process ended, about to start another one
13:55:20.883 probes.py         DEBUG  attempt no. 2 started, pid: 463
13:55:20.884 probes.py         DEBUG  pausing for 1 before next try
13:55:20.887 probes.py         DEBUG  Running "functools.partial(<bound method DockerContainer.is_port_open of DockerContainer(image=registry.fedoraproject.org/fedora:27, id=4931a079dbf3d52f39f5a530f5bc0025130146b7463f2543f2d8bce5379bd106)>, 8765)" with parameters: "{}":       1/10
13:55:20.899 __init__.py       INFO   trying to open connection to 172.17.0.2:8765
13:55:20.900 __init__.py       INFO   was connection successful? errno: 0
13:55:20.900 __init__.py       DEBUG  port is opened: 172.17.0.2:8765
13:55:24.193 container.py      DEBUG  ['atomic', 'mount', '4931a079dbf3d52f39f5a530f5bc0025130146b7463f2543f2d8bce5379bd106', '/tmp/conur9nsvcyz']
13:55:24.193 __init__.py       DEBUG  command: ['atomic', 'mount', '4931a079dbf3d52f39f5a530f5bc0025130146b7463f2543f2d8bce5379bd106', '/tmp/conur9nsvcyz']
13:55:25.038 filesystem.py     DEBUG  path = /tmp/conur9nsvcyz/etc/passwd
13:55:25.038 __init__.py       DEBUG  command: ['atomic', 'umount', '/tmp/conur9nsvcyz']
```

The test passed! The logs should be easy to read, so you should have pretty good overview of what happened.


# Documentation
For more info see our documentation at [conu.readthedocs.io](http://conu.readthedocs.io/en/latest/).

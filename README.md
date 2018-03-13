# conu

`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

![example](./docs/example.gif)

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
- check all packages in image are signed with a key

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
#!/usr.bin/python3
import logging
import os

from conu import DockerRunBuilder, DockerBackend, random_str, Directory


# this is the port where we can access our app
port = 8765


# convenience function to run our application - webserver
def run_container(backend, local_dir):
    """
    serve path `local_dir` using the python http webserver in a docker container

    :param backend: DockerBackend instance
    :param local_dir: str, path to the directory, it should exist
    :return: instance of DockerContainer
    """
    image_name = "registry.fedoraproject.org/fedora"
    image_tag = "27"

    # we'll run our container using docker engine
    # the image will be pulled if it's not present locally (default behavior)
    image = backend.ImageClass(image_name, tag=image_tag)

    # helper class to create `docker run ...` -- we want test the same experience as our users
    b = DockerRunBuilder(
        # the command to run in a container
        command=["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port],
        # additional options passed to `run` command
        additional_opts=["-v", "%s:/webroot" % local_dir, "-w", "/webroot"]
    )
    # let's run the container (in the background)
    container = image.run_via_binary(run_command_instance=b)
    return container


def test_webserver():
    # let's setup the directory to serve first
    temp_dir_name = "shiny-%s" % random_str()
    temp_dir_path = os.path.join("/tmp", temp_dir_name)
    with DockerBackend(logging_level=logging.DEBUG) as backend:
        # helper class to create and initialize the dir -- will be removed once we
        # leave the context manager
        with Directory(temp_dir_path, mode=0o0700):
            # let's put some file in it
            with open(os.path.join(temp_dir_path, "candle"), "w") as fd:
                fd.write("You no take candle!")
            container = run_container(backend, temp_dir_path)
            try:
                # we need to wait for the webserver to start serving
                container.wait_for_port(port)
                # GET on /
                http_response = container.http_request(path="/", port=port)
                assert http_response.ok
                assert '<a href="candle">candle</a>' in http_response.content.decode("utf-8")
                # now GETting the file
                assert 'You no take candle!' in container.http_request(
                    path="/candle", port=port).content.decode("utf-8")
            finally:
                container.kill()
                container.delete()


test_webserver()
```

Let's run it! Please make sure that you run the provided example as root, since
`conu` utilizes [`atomic`](https://github.com/projectatomic/atomic) tool and its `mount` command, which requires you to
be root.

Let's run it and look at the logs:
```bash
$ python3 ./example.py
```
```
13:32:17.668 backend.py        INFO   conu has initiated, welcome to the party!
13:32:17.668 backend.py        DEBUG  conu version: 0.1.0
13:32:17.669 filesystem.py     INFO   initializing Directory(path=/tmp/shiny-kbjmsxgett)
13:32:17.669 filesystem.py     DEBUG  changing permission bits of /tmp/shiny-kbjmsxgett to 0o700
13:32:17.669 filesystem.py     INFO   initialized
13:32:17.676 image.py          INFO   run container via binary in background
13:32:17.676 image.py          DEBUG  docker command: ['docker', 'container', 'run', '-v', '/tmp/shiny-kbjmsxgett:/webroot', '-w', '/webroot', '-d', '--cidfile=/tmp/conu-b3jluxsc/conu-cbtbokqsedrtmiktfawbozgczdgxktmt', '-l', 'conu.test_artifact', 'sha256:9881e4229c9517b592980740ab2dfd8b5176adf7eb3be0f32b10a5dac5a3f12a', 'python3', '-m', 'http.server', '--bind', '0.0.0.0', '8765']
13:32:17.676 __init__.py       DEBUG  command: ['docker', 'container', 'run', '-v', '/tmp/shiny-kbjmsxgett:/webroot', '-w', '/webroot', '-d', '--cidfile=/tmp/conu-b3jluxsc/conu-cbtbokqsedrtmiktfawbozgczdgxktmt', '-l', 'conu.test_artifact', 'sha256:9881e4229c9517b592980740ab2dfd8b5176adf7eb3be0f32b10a5dac5a3f12a', 'python3', '-m', 'http.server', '--bind', '0.0.0.0', '8765']
6a0530ab32c17858180c9c3867c17a2aaf3466c6dd17c329ab7a0cf9d991f626
13:32:18.131 probes.py         DEBUG  starting probe
13:32:18.137 probes.py         DEBUG  Running "<lambda>" with parameters: "{}": 0/10
13:32:18.133 probes.py         DEBUG  first process started: pid=5812
13:32:18.141 probes.py         DEBUG  pausing for 0.1 before next try
13:32:18.243 probes.py         DEBUG  starting probe
13:32:18.244 probes.py         DEBUG  first process started: pid=5828
13:32:18.245 probes.py         DEBUG  pausing for 1 before next try
13:32:18.246 probes.py         DEBUG  Running "functools.partial(<bound method DockerContainer.is_port_open of DockerContainer(image=registry.fedoraproject.org/fedora:27, id=6a0530ab32c17858180c9c3867c17a2aaf3466c6dd17c329ab7a0cf9d991f626)>, 8765)" with parameters: "{}":      0/10
13:32:18.251 __init__.py       INFO   trying to open connection to 172.17.0.2:8765
13:32:18.251 __init__.py       INFO   was connection successful? errno: 0
13:32:18.251 __init__.py       DEBUG  port is opened: 172.17.0.2:8765
13:32:19.444 filesystem.py     INFO   brace yourselves, removing '/tmp/shiny-kbjmsxgett'
```

The test passed! The logs should be easy to read, so you should have pretty good overview of what happened.


# Real examples

- [postgresql image](https://github.com/container-images/postgresql/tree/master/test)
- [ruby image](https://github.com/container-images/ruby/blob/master/test/test_s2i.py)
- [memcached image](https://github.com/container-images/memcached/blob/master/tests/memcached_conu.py)
- [php image](https://github.com/sclorg/s2i-php-container/pull/198)
- [tools image](https://github.com/container-images/tools/pull/5)


# Documentation
For more info see our documentation at [conu.readthedocs.io](http://conu.readthedocs.io/en/latest/).

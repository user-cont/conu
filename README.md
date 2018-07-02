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

## Docker container

You can try conu also in the container, but you have to:
- mount docker socket
- use `--cap-add SYS_ADMIN` for mounting containers/images
- set `--privileged` option or turn off the selinux to allow access to docker inside the container:

```
docker run -it --rm \
-v /var/run/docker.sock:/var/run/docker.sock:z \
--cap-add SYS_ADMIN \
--privileged \
modularitycontainers/conu:0.2.0 python3
```

```python
>>> from conu import DockerBackend
>>> backend = DockerBackend()
11:52:13.022 backend.py        INFO   conu has initiated, welcome to the party!
>>> image = backend.ImageClass('docker.io/library/nginx')
11:52:32.562 __init__.py       INFO   docker environment info: ...
>>> container = image.run_via_binary()
11:52:51.910 image.py          INFO   run container via binary in background
```

If you want to run custom source file, mount it to the container in the following way:

```
docker run -it --rm \
-v /var/run/docker.sock:/var/run/docker.sock:z \
-v $PWD/my_source.py:/app/my_source.py:z \
--cap-add SYS_ADMIN \
--privileged \
modularitycontainers/conu:0.2.0 python3 /app/my_source.py
```

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
$ cat examples/readme_webserver.py
```
```python
#!/usr/bin/python3

import logging

from conu import DockerRunBuilder, DockerBackend

# our webserver will be accessible on this port
port = 8765

# we'll utilize this container image
image_name = "registry.fedoraproject.org/fedora"
image_tag = "27"

# we'll run our container using docker engine
with DockerBackend(logging_level=logging.DEBUG) as backend:
    # the image will be pulled if it's not present
    image = backend.ImageClass(image_name, tag=image_tag)

    # the command to run in a container
    command = ["python3", "-m", "http.server", "--bind", "0.0.0.0", "%d" % port]
    # let's run the container (in the background)
    container = image.run_via_binary(command=command)
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

Let's run it and look at the logs:
```bash
$ python3 examples/readme_webserver.py
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

# Kubernetes

## Use conu with minikube locally

If you want to test your images in Kubernetes locally, you will need to run kubernetes cluster on your host. We recommend to use minikube, for installation follow instructions in [minikube github repository](https://github.com/kubernetes/minikube).

After just run:
```bash
$ minikube start --extra-config=apiserver.admission-control=""
```

## Kubernetes example

```bash
$ cat examples/k8s_deployment.py
```

```python
from conu.backend.k8s.backend import K8sBackend
from conu.backend.k8s.deployment import Deployment

with K8sBackend() as k8s_backend:
    namespace = k8s_backend.create_namespace()

    template = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: nginx-deployment
      labels:
        app: nginx
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: nginx
      template:
        metadata:
          labels:
            app: nginx
        spec:
          containers:
          - name: nginx
            image: nginx:1.7.9
            ports:
            - containerPort: 80
    """

    test_deployment = Deployment(namespace=namespace, from_template=template,
                                 create_in_cluster=True)

    try:
        test_deployment.wait(200)
        assert test_deployment.all_pods_ready()
    finally:
        test_deployment.delete()
        k8s_backend.delete_namespace(namespace)

```

Let's run it and look at the logs:

``` bash
$ python3 examples/k8s_deployment.py
```
```
11:35:04.753 backend.py        INFO   conu has initiated, welcome to the party!
11:35:04.850 backend.py        INFO   Creating namespace: namespace-ty1a
11:35:04.885 deployment.py     INFO   Creating Deployment nginx-deployment in namespace: namespace-ty1a
11:36:04.910 deployment.py     INFO   All pods are ready for deployment nginx-deployment in namespace: namespace-ty1a
11:36:04.923 deployment.py     INFO   Deleting Deployment nginx-deployment in namespace: namespace-ty1a
11:36:04.935 backend.py        INFO   Deleting namespace: namespace-ty1a
```

# Real examples

- [postgresql image](https://github.com/container-images/postgresql/tree/master/test)
- [ruby image](https://github.com/container-images/ruby/blob/master/test/test_s2i.py)
- [memcached image](https://github.com/container-images/memcached/blob/master/tests/memcached_conu.py)
- [php image](https://github.com/sclorg/s2i-php-container/pull/198)
- [tools image](https://github.com/container-images/tools/pull/5)


# Documentation
For more info see our documentation at [conu.readthedocs.io](http://conu.readthedocs.io/en/latest/).

# conu
![PyPI](https://img.shields.io/pypi/v/conu.svg)
![PyPI - License](https://img.shields.io/pypi/l/conu.svg)
![PyPI - Status](https://img.shields.io/pypi/status/conu.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/427eb0c5dfc040cea798b23575dba025)](https://www.codacy.com/app/user-cont/conu?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=user-cont/conu&amp;utm_campaign=Badge_Grade)
[![Build Status](https://ci.centos.org/job/user-cont-conu-master/badge/icon)](https://ci.centos.org/job/user-cont-conu-master/)


`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

`conu` is supported on python 3.6+ only.

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
$ dnf install python3-conu
```

Please visit [our documentation](http://conu.readthedocs.io/en/latest/installation.html) for more info on installation.

## Docker container

You can try conu also in the container, but you have to:
- mount docker socket
- use `--cap-add SYS_ADMIN` for mounting containers/images
- set `--privileged` option or turn off the SELinux to allow access to docker inside the container:

```
docker run -it --rm \
-v /var/run/docker.sock:/var/run/docker.sock:z \
--cap-add SYS_ADMIN \
--privileged \
usercont/conu:0.6.0 python3
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
usercont/conu:0.6.0 python3 /app/my_source.py
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
- run image inside Kubernetes pod

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

## Kubernetes
- create/delete new namespace
- create/delete Pod
- create/delete Deployment
    - with parameters
    - from template
- create/delete Service
- shortcut methods for getting:
    - pod logs
    - pod IP
    - pod phase
    - pod condition
    - service IP
- perform checks whether
    - pod is ready  
    - all pods are ready for specific deployment

## OpenShift
- create new app using `oc new-app` command
    - deploy pure image into openshift
    - support building s2i images from remote repository
    - support building s2i images from local path
    - support creating new applications using OpenShift templates
- push images to internal OpenShift registry
- request service
- waiting until service is ready
- obtain logs from all pods
- get status of application
- check readiness of pods
- cleanup objects of specific application in current namespace 

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

After that, run minikube like this:
```bash
$ minikube start
```

## Kubernetes example

```bash
$ cat examples/k8s_deployment.py
```

```python
from conu.backend.k8s.backend import K8sBackend
from conu.backend.k8s.deployment import Deployment
from conu.utils import get_oc_api_token

# obtain API key from OpenShift cluster. If you are not using OpenShift cluster for kubernetes tests
# you need to replace `get_oc_api_token()` with your Bearer token. More information here:
# https://kubernetes.io/docs/reference/access-authn-authz/authentication/
api_key = get_oc_api_token()

with K8sBackend(api_key=api_key) as k8s_backend:

    namespace = k8s_backend.create_namespace()

    template = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hello-world
      labels:
        app: hello-world
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: hello-world
      template:
        metadata:
          labels:
            app: hello-world
        spec:
          containers:
          - name: hello-openshift
            image: openshift/hello-openshift
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
13:23:09.479 backend.py        INFO   conu has initiated, welcome to the party!
13:23:09.523 backend.py        INFO   Creating namespace: namespace-m4cz
13:23:14.557 backend.py        INFO   Namespace is ready!
13:23:19.562 deployment.py     INFO   Creating Deployment hello-world in namespace: namespace-m4cz
13:23:27.625 deployment.py     INFO   All pods are ready for deployment hello-world in namespace: namespace-m4cz
13:23:28.620 deployment.py     INFO   Deleting Deployment hello-world in namespace: namespace-m4cz
13:23:28.654 backend.py        INFO   Deleting namespace: namespace-m4cz
```

# Openshift

## Use conu for testing locally

If you want to test your images in OpenShift locally, you need to run OpenShift cluster on your host. You can install it by following instructions in OpenShift [origin](https://github.com/openshift/origin/) or [minishift](https://github.com/minishift/minishift) github repositories.

After that, you may need to setup cluster, here is example setup:
``` bash
oc cluster up
oc login -u system:admin
oadm policy add-role-to-user system:registry developer
oadm policy add-role-to-user admin developer
oadm policy add-role-to-user system:image-builder developer
oadm policy add-cluster-role-to-user cluster-reader developer
oadm policy add-cluster-role-to-user admin developer
oadm policy add-cluster-role-to-user cluster-admin developer
oc login -u developer -p developer
```

For more information, why do you need to grant all these rights to user see [accessing registry](https://docs.openshift.com/container-platform/3.3/install_config/registry/accessing_registry.html#access-user-prerequisites)

## OpenShift example
``` bash
$ cat examples/oepnshift/openshift_s2i_remote.py
```

```python
import logging

from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend
from conu.utils import get_oc_api_token

api_key = get_oc_api_token()
with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:
    with DockerBackend(logging_level=logging.DEBUG) as backend:
        # builder image
        python_image = backend.ImageClass("centos/python-36-centos7")

        # docker login inside OpenShift internal registry
        OpenshiftBackend.login_to_registry('developer')

        # create new app from remote source in OpenShift cluster
        app_name = openshift_backend.new_app(python_image,
                                             source="https://github.com/openshift/django-ex.git",
                                             project='myproject')

        try:
            # wait until service is ready to accept requests
            openshift_backend.wait_for_service(
                app_name=app_name,
                expected_output='Welcome to your Django application on OpenShift',
                timeout=300)
        finally:
            openshift_backend.clean_project(app_name)

```

Let's run it and look at the logs:

``` bash
$ python3 examples/openshift/openshift_s2i_remote.py
```

```
13:29:38.231 backend.py        INFO   conu has initiated, welcome to the party!
13:29:38.231 backend.py        DEBUG  conu version: 0.5.0
13:29:38.256 backend.py        INFO   conu has initiated, welcome to the party!
13:29:38.256 backend.py        DEBUG  conu version: 0.5.0
13:29:38.314 __init__.py       INFO   docker environment info: 'Client:\n Version:         1.13.1\n API version:     1.26\n Package version: docker-1.13.1-74.git6e3bb8e.el7.centos.x86_64\n Go version:      go1.10.3\n Git commit:      1556cce-unsupported\n Built:           Wed Aug  1 17:21:17 2018\n OS/Arch:         linux/amd64\n\nServer:\n Version:         1.13.1\n API version:     1.26 (minimum version 1.12)\n Package version: docker-1.13.1-74.git6e3bb8e.el7.centos.x86_64\n Go version:      go1.9.4\n Git commit:      6e3bb8e/1.13.1\n Built:           Tue Aug 21 15:23:37 2018\n OS/Arch:         linux/amd64\n Experimental:    false\n'
13:29:38.326 backend.py        INFO   conu has initiated, welcome to the party!
13:29:38.584 backend.py        INFO   conu has initiated, welcome to the party!
13:29:38.656 backend.py        INFO   Login to 172.30.1.1:5000 succeed
13:29:38.656 backend.py        INFO   conu has initiated, welcome to the party!
13:29:38.673 image.py          INFO   The push refers to a repository [172.30.1.1:5000/myproject/python-36-centos7]
13:29:38.689 image.py          INFO   Preparing
13:29:38.689 image.py          INFO   Preparing
13:29:38.689 image.py          INFO   Preparing
13:29:38.690 image.py          INFO   Preparing
13:29:38.690 image.py          INFO   Preparing
13:29:38.690 image.py          INFO   Preparing
13:29:38.690 image.py          INFO   Preparing
13:29:38.690 image.py          INFO   Preparing
13:29:38.690 image.py          INFO   Preparing
13:29:38.700 image.py          INFO   Waiting
13:29:38.701 image.py          INFO   Waiting
13:29:38.701 image.py          INFO   Waiting
13:29:38.701 image.py          INFO   Waiting
13:29:38.747 image.py          INFO   Layer already exists
13:29:38.747 image.py          INFO   Layer already exists
13:29:38.753 image.py          INFO   Layer already exists
13:29:38.754 image.py          INFO   Layer already exists
13:29:38.772 image.py          INFO   Layer already exists
13:29:38.807 image.py          INFO   Layer already exists
13:29:38.807 image.py          INFO   Layer already exists
13:29:38.807 image.py          INFO   Layer already exists
13:29:38.807 image.py          INFO   Layer already exists
13:29:39.065 image.py          INFO   latest: digest: sha256:51cf14c1d1491c5ab0e902c52740c22d4fff52f95111b97d195d12325a426350 size: 2210
13:29:39.065 backend.py        INFO   Creating new app in project myproject
13:29:39.558 backend.py        INFO   Waiting for service to get ready
13:30:06.768 backend.py        INFO   Connection to service established and return expected output!
13:30:07.729 backend.py        INFO   Deleting app
13:30:09.504 backend.py        INFO   deploymentconfig "app-u4ow" deleted
13:30:09.504 backend.py        INFO   buildconfig "app-u4ow" deleted
13:30:09.504 backend.py        INFO   imagestream "app-u4ow" deleted
13:30:09.504 backend.py        INFO   pod "app-u4ow-1-vltwq" deleted
13:30:09.504 backend.py        INFO   service "app-u4ow" deleted

```

# Real examples

- [postgresql image](https://github.com/container-images/postgresql/tree/master/test)
- [ruby image](https://github.com/container-images/ruby/blob/master/test/test_s2i.py)
- [memcached image](https://github.com/container-images/memcached/blob/master/tests/memcached_conu.py)
- [php image](https://github.com/sclorg/s2i-php-container/pull/198)
- [tools image](https://github.com/container-images/tools/pull/5)


# Documentation
For more info see our documentation at [conu.readthedocs.io](http://conu.readthedocs.io/en/latest/).

# How to release conu

We are using awesome [release-bot](https://github.com/user-cont/release-bot) for new conu releases.
If you want to make new release:

- create new issue with title `x.y.z release` and wait for release bot to create new PR.
- polish **CHANGELOG.md** and merge if tests are passing.
- Sit down, relax and watch how release bot is doing the hard work.

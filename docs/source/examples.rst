Examples
=========

Run a container
----------------

For running a container, you need to have image initialized. Image holds information of repository and tag and provides other methods. To run image using docker binary (as user would) use :func:`conu.apidefs.image.Image.run_via_binary` method with :class:`conu.backend.docker.container.DockerRunBuilder` as parameter.

.. include:: examples/run_image.py
   :code: python
   :start-line: 17
   :end-line: 27

Wait for service to be ready
----------------------------

:func:`conu.backend.docker.container.DockerContainer.wait_for_port` tries to reach 8080 till it's opened. You can use your own timeout to limit time spent on waiting.

.. include:: examples/check_port.py
   :code: python
   :start-line: 16
   :end-line: 26

Extend image using source-to-image
-----------------------------------

Extends acts as s2i binary. It extends builder image in form of :class:`conu.backend.docker.image.S2IDockerImage` using provided source and desired name of resulting image.

.. include:: examples/s2i.py
   :code: python
   :start-line: 16
   :end-line: 28

Run image in pod
----------------
Run image inside k8s :class:`conu.backend.k8s.pod.Pod`

.. include:: examples/k8s_pod.py
   :code: python
   :start-line: 16
   :end-line: 42

Deploy new application in OpenShift using remote source
-------------------------------------------------------

Build and deploy new application in OpenShift using ``centos/python-36-centos7`` image and remote source.

.. include:: examples/openshift/openshift_s2i_remote.py
   :code: python
   :start-line: 16
   :end-line: 45
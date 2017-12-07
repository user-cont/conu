Examples
=========

Run a container
----------------

For running a container, you need to have image initialized. Image holds information of repository and tag and provides other methods. To run image using docker binary (as user would) use :func:`conu.apidefs.image.Image.run_via_binary` method with :class:`conu.backend.docker.container.DockerRunBuilder` as parameter.

.. include:: examples/run_image.py
   :code: python
   :start-line: 3
   :end-line: 7

Wait for service to be ready
----------------------------

:func:`conu.backend.docker.container.DockerContainer.wait_for_port` tries to reach 8080 till it's opened. You can use your own timeout to limit time spent on waiting.

.. include:: examples/check_port.py
   :code: python
   :start-line: 3
   :end-line: 8

Extend image using source-to-image
-----------------------------------

Extends acts as s2i binary. It extends builder image in form of :class:`conu.backend.docker.image.S2IDockerImage` using provided source and desired name of resulting image.

.. include:: examples/s2i.py
   :code: python
   :start-line: 3
   :end-line: 8

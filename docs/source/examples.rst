Examples
=========

Run a container
----------------

For running a container, you need to have image initialized. Image holds information of repository and tag and provides other methods. To run image using docker binary (as user would) use run_via_binary method with image and DockerRunCommand as parameters.

.. include:: examples/run_image.py
   :code: python
   :start-line: 3

Wait for service to be ready
----------------------------

wait_for_port tries to reach 8080 till it's opened. You can use your own timeout to limit time spent on waiting.

.. include:: examples/check_port.py
   :code: python
   :start-line: 3

Inject own binary into a container
-----------------------------------

TBD

Extend image using source-to-image
-----------------------------------

Extends acts as s2i binary. It extends builder image in form od S2IDockerImage using provided source and desired name of resulting image.

.. include:: examples/s2i.py
   :code: python
   :start-line: 3

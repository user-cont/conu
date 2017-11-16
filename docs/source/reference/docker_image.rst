Docker Image
=============

Aside from methods in API definition - :class:`conu.apidefs.image.Image`, DockerImage implements following methods:

.. autoclass:: conu.backend.docker.image.DockerImage
   :members: inspect, tag_image

.. autoclass:: conu.backend.docker.image.DockerImageFS
   :members:

Aside from methods in API definition - :class:`conu.apidefs.image.S2Image`, S2IDockerImage implements following methods:

.. autoclass:: conu.backend.docker.image.S2IDockerImage
   :members: s2i_exists


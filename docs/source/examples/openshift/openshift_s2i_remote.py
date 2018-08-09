import logging

from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend

with OpenshiftBackend(logging_level=logging.DEBUG) as openshift_backend:
    with DockerBackend() as backend:
        # builder image
        python_image = backend.ImageClass("centos/python-36-centos7")

        # docker login inside OpenShift internal registry
        openshift_backend.login_to_registry('developer')

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

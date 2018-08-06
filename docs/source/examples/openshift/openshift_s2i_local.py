import logging
from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend

with OpenshiftBackend(logging_level=logging.DEBUG) as openshift_backend:
    with DockerBackend() as backend:
        # builder image
        python_image = backend.ImageClass("centos/python-36-centos7")

        # docker login inside OpenShift internal registry
        openshift_backend.login_registry()

        # create new app from local source in OpenShift cluster
        app_name = openshift_backend.new_app(python_image,
                                             source="examples/openshift/standalone-test-app",
                                             project='myproject')

        try:
            # wait until service is ready to accept requests
            openshift_backend.wait_for_service(
                app_name=app_name,
                expected_output="Hello World from standalone WSGI application!")
        finally:
            openshift_backend.clean_project()

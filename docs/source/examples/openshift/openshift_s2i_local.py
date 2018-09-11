import logging

from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend
from conu.utils import run_cmd

api_key = run_cmd(["oc", "whoami", "-t"], return_output=True).rstrip()
with OpenshiftBackend(api_key=api_key, logging_level=logging.DEBUG) as openshift_backend:
    with DockerBackend(logging_level=logging.DEBUG) as backend:
        # builder image
        python_image = backend.ImageClass("centos/python-36-centos7")

        # docker login inside OpenShift internal registry
        openshift_backend.login_to_registry('developer')

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
            openshift_backend.clean_project(app_name)

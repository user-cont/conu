from conu.backend.origin.backend import OpenshiftBackend
from conu.backend.docker.backend import DockerBackend

with OpenshiftBackend(logging_level=logging.DEBUG) as openshift_backend:
    with DockerBackend() as backend:

        # images that this template uses
        python_image = backend.ImageClass("centos/python-36-centos7", tag="latest")
        psql_image = backend.ImageClass("centos/postgresql-96-centos7", tag="9.6")

        # docker login inside OpenShift internal registry
        openshift_backend.login_to_registry('developer')

        # create new app from remote source in OpenShift cluster
        app_name = openshift_backend.new_app(
            image=python_image,
            template="https://raw.githubusercontent.com/sclorg/django-ex"
                     "/master/openshift/templates/django-postgresql.json",
            oc_new_app_args=["-p", "SOURCE_REPOSITORY_REF=master", "-p", "PYTHON_VERSION=3.6",
                             "-p", "POSTGRESQL_VERSION=9.6"],
            name_in_template={"python": "3.6"},
            other_images=[{psql_image: "postgresql:9.6"}],
            project='myproject')

        try:
            # wait until service is ready to accept requests
            openshift_backend.wait_for_service(
                app_name=app_name,
                expected_output='Welcome to your Django application on OpenShift')
        finally:
            openshift_backend.clean_project(app_name)

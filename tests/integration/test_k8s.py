# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Tests for Kubernetes backend
"""

import urllib3
import pytest

from conu import DockerBackend, \
                 K8sBackend, K8sCleanupPolicy
from conu.backend.k8s.pod import Pod, PodPhase
from conu.backend.k8s.service import Service
from conu.backend.k8s.deployment import Deployment
from conu.backend.k8s.client import get_core_api
from conu.utils import get_oc_api_token, oc_command_exists, is_oc_cluster_running

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.mark.skipif(not oc_command_exists(), reason="OpenShift is not installed!")
@pytest.mark.skipif(not is_oc_cluster_running(), reason="OpenShift cluster is not running!")
class TestK8s(object):

    def test_pod(self):
        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:

            namespace = k8s_backend.create_namespace()

            with DockerBackend() as backend:
                image = backend.ImageClass("openshift/hello-openshift")

                pod = image.run_in_pod(namespace=namespace)

                try:
                    pod.wait(200)
                    assert pod.is_ready()
                    assert pod.get_phase() == PodPhase.RUNNING
                finally:
                    pod.delete()
                    assert pod.get_phase() == PodPhase.TERMINATING
                    k8s_backend.delete_namespace(namespace)

    def test_pod_from_template(self):

        template = {
          "apiVersion": "v1",
          "kind": "Pod",
          "metadata": {
            "name": "myapp-pod",
            "labels": {
              "app": "myapp"
            }
          },
          "spec": {
            "containers": [
              {
                "name": "myapp-container",
                "image": "busybox",
                "command": [
                  "sh",
                  "-c",
                  "echo Hello Kubernetes! && sleep 3600"
                ]
              }
            ]
          }
        }

        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:
            namespace = k8s_backend.create_namespace()

            pod = Pod(namespace=namespace, from_template=template)

            try:
                pod.wait(200)
                assert pod.is_ready()
                assert pod.get_phase() == PodPhase.RUNNING
            finally:
                pod.delete()
                assert pod.get_phase() == PodPhase.TERMINATING
                k8s_backend.delete_namespace(namespace)

    def test_database_deployment(self):
        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:

            namespace = k8s_backend.create_namespace()

            with DockerBackend() as backend:
                postgres_image = backend.ImageClass("centos/postgresql-10-centos7")

                postgres_image_metadata = postgres_image.get_metadata()

                # set up env variables
                db_env_variables = {"POSTGRESQL_USER": "user",
                                    "POSTGRESQL_PASSWORD": "pass",
                                    "POSTGRESQL_DATABASE": "db"}

                postgres_image_metadata.env_variables.update(db_env_variables)

                db_labels = {"app": "postgres"}

                db_service = Service(name="database", ports=["5432"], selector=db_labels,
                                     namespace=namespace,
                                     create_in_cluster=True)

                db_deployment = Deployment(name="database", selector=db_labels, labels=db_labels,
                                           image_metadata=postgres_image_metadata,
                                           namespace=namespace,
                                           create_in_cluster=True)

                try:
                    db_deployment.wait(200)
                    assert db_deployment.all_pods_ready()
                finally:
                    db_deployment.delete()
                    db_service.delete()
                    k8s_backend.delete_namespace(namespace)

    def test_list_pods(self):
        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:

            namespace = k8s_backend.create_namespace()

            with DockerBackend() as backend:

                image = backend.ImageClass("openshift/hello-openshift")

                pod = image.run_in_pod(namespace=namespace)

                try:
                    pod.wait(200)
                    assert any(pod.name == p.name for p in k8s_backend.list_pods())
                finally:
                    pod.delete()
                    k8s_backend.delete_namespace(namespace)

    def test_list_services(self):
        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:

            namespace = k8s_backend.create_namespace()

            labels = {"app": "postgres"}

            service = Service(name="database", ports=["5432"], selector=labels, namespace=namespace,
                              create_in_cluster=True)

            try:
                assert any(service.name == s.name for s in k8s_backend.list_services())
            finally:
                service.delete()
                k8s_backend.delete_namespace(namespace)

    def test_list_deployments(self):
        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:

            namespace = k8s_backend.create_namespace()

            with DockerBackend() as backend:
                postgres_image = backend.ImageClass("centos/postgresql-10-centos7")

                postgres_image_metadata = postgres_image.get_metadata()

                # set up env variables
                db_env_variables = {"POSTGRESQL_USER": "user",
                                    "POSTGRESQL_PASSWORD": "pass",
                                    "POSTGRESQL_DATABASE": "db"}

                postgres_image_metadata.env_variables.update(db_env_variables)

                db_labels = {"app": "postgres"}

                db_deployment = Deployment(name="database", selector=db_labels, labels=db_labels,
                                           image_metadata=postgres_image_metadata,
                                           namespace=namespace,
                                           create_in_cluster=True)

                try:
                    db_deployment.wait(200)
                    assert db_deployment.all_pods_ready()
                    assert any(db_deployment.name == d.name for d in k8s_backend.list_deployments())
                finally:
                    db_deployment.delete()
                    k8s_backend.delete_namespace(namespace)

    def test_list_pod_for_namespace(self):
        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key) as k8s_backend:
            namespace1 = k8s_backend.create_namespace()
            namespace2 = k8s_backend.create_namespace()

            with DockerBackend() as backend:

                image = backend.ImageClass("openshift/hello-openshift")

                pod1 = image.run_in_pod(namespace=namespace1)

                try:
                    pod1.wait(200)
                    assert any(pod1.name == p.name for p in k8s_backend.list_pods(namespace1))
                    assert not any(pod1.name == p.name for p in k8s_backend.list_pods(namespace2))
                finally:
                    pod1.delete()
                    k8s_backend.delete_namespace(namespace1)
                    k8s_backend.delete_namespace(namespace2)

    def test_deployment_from_template(self):
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

    def test_cleanup(self):

        api = get_core_api()

        # take just namespaces that are not in terminating state
        number_of_namespaces = len(
            [item for item in api.list_namespace().items if item.status.phase != "Terminating"])

        api_key = get_oc_api_token()
        with K8sBackend(api_key=api_key, cleanup=[K8sCleanupPolicy.NAMESPACES]) as k8s_backend:

            # create two namespaces
            k8s_backend.create_namespace()
            k8s_backend.create_namespace()

        # cleanup should delete two namespaces created with k8s backend
        assert len(
            [item for item in api.list_namespace().items
             if item.status.phase != "Terminating"]) == number_of_namespaces

        with K8sBackend(api_key=api_key) as k8s_backend:

            # create two namespaces
            k8s_backend.create_namespace()
            k8s_backend.create_namespace()

        # no cleanup - namespaces are not deleted after work with backend is finished
        assert len(
            [item for item in api.list_namespace().items
             if item.status.phase != "Terminating"]) == number_of_namespaces + 2

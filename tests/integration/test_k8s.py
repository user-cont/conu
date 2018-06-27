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

import pytest

from conu import DockerBackend
from conu.backend.k8s.backend import K8sBackend
from conu.backend.k8s.pod import PodPhase
from conu.backend.k8s.service import Service
from conu.backend.k8s.deployment import Deployment

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.mark.xfail
def test_pod():
    with K8sBackend() as k8s_backend:

        namespace = k8s_backend.create_namespace()

        with DockerBackend() as backend:
            image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

            pod = image.run_in_pod(namespace=namespace)

            try:
                pod.wait(200)
                assert pod.get_phase() == PodPhase.RUNNING
            finally:
                pod.delete()
                assert pod.get_phase() == PodPhase.TERMINATING
                k8s_backend.delete_namespace(namespace)


@pytest.mark.xfail
def test_database_deployment():
    with K8sBackend() as k8s_backend:

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
                                       image_metadata=postgres_image_metadata, namespace=namespace,
                                       create_in_cluster=True)

            try:
                db_deployment.wait(200)
                assert db_deployment.all_pods_ready()
            finally:
                db_deployment.delete()
                db_service.delete()
                k8s_backend.delete_namespace(namespace)


@pytest.mark.xfail
def test_list_pods():
    with K8sBackend() as k8s_backend:

        namespace = k8s_backend.create_namespace()

        with DockerBackend() as backend:

            image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

            pod = image.run_in_pod(namespace=namespace)

            try:
                pod.wait(200)
                assert any(pod.name == p.name for p in k8s_backend.list_pods())
            finally:
                pod.delete()
                k8s_backend.delete_namespace(namespace)


def test_list_services():
    with K8sBackend() as k8s_backend:

        namespace = k8s_backend.create_namespace()

        labels = {"app": "postgres"}

        service = Service(name="database", ports=["5432"], selector=labels, namespace=namespace,
                          create_in_cluster=True)

        try:
            assert any(service.name == s.name for s in k8s_backend.list_services())
        finally:
            service.delete()
            k8s_backend.delete_namespace(namespace)


@pytest.mark.xfail
def test_list_deployments():
    with K8sBackend() as k8s_backend:

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
                                       image_metadata=postgres_image_metadata, namespace=namespace,
                                       create_in_cluster=True)

            try:
                db_deployment.wait(200)
                assert db_deployment.all_pods_ready()
                assert any(db_deployment.name == d.name for d in k8s_backend.list_deployments())
            finally:
                db_deployment.delete()
                k8s_backend.delete_namespace(namespace)

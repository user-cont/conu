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
from conu.backend.k8s.pod import PodPhase
from conu.backend.k8s.service import Service
from conu.backend.k8s.deployment import Deployment

from ..constants import FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG


@pytest.mark.xfail
def test_pod():
    with DockerBackend() as backend:
        image = backend.ImageClass(FEDORA_MINIMAL_REPOSITORY, tag=FEDORA_MINIMAL_REPOSITORY_TAG)

        pod = image.run_in_pod(namespace='default')

        try:
            pod.wait(200)
            assert pod.get_phase() == PodPhase.RUNNING
        finally:
            pod.delete()
            assert pod.get_phase() == PodPhase.TERMINATING


@pytest.mark.xfail
def test_database_deployment():
    with DockerBackend() as backend:
        postgres_image = backend.ImageClass("centos/postgresql-10-centos7")

        postgres_image_metadata = postgres_image.get_metadata()

        # set up env variables

        db_env_variables = {"POSTGRESQL_USER": "user",
                            "POSTGRESQL_PASSWORD": "pass",
                            "POSTGRESQL_DATABASE": "db"}

        postgres_image_metadata.env_variables.update(db_env_variables)

        db_labels = {"app": "postgres"}

        db_service = Service(name="database", ports=["5432"], selector=db_labels)

        db_deployment = Deployment(name="database", selector=db_labels, labels=db_labels,
                                   image_metadata=postgres_image_metadata)

        try:
            db_deployment.wait(200)
            assert db_deployment.all_pods_ready()
        finally:
            db_deployment.delete()
            db_service.delete()

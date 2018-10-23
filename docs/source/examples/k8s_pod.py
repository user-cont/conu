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

import logging

from conu import K8sBackend, \
                 DockerBackend
from conu.backend.k8s.pod import PodPhase
from conu.utils import get_oc_api_token

api_key = get_oc_api_token()
with K8sBackend(api_key=api_key, logging_level=logging.DEBUG) as k8s_backend:

    namespace = k8s_backend.create_namespace()

    with DockerBackend(logging_level=logging.DEBUG) as backend:
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

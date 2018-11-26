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
TODO: add docs here, so `help(conu)` looks good
"""
# docker backend
from conu.backend.docker.backend import DockerBackend
from conu.backend.docker.container import (
    DockerContainer, DockerRunBuilder, DockerContainerViaExportFS
)
from conu.backend.docker.image import (
    DockerImage, S2IDockerImage, DockerImagePullPolicy, DockerImageViaArchiveFS
)

# podman backend
from conu.backend.podman.backend import PodmanBackend
from conu.backend.podman.container import PodmanContainer, PodmanRunBuilder
from conu.backend.podman.image import PodmanImage, PodmanImagePullPolicy

# k8s backend
from conu.backend.k8s.backend import K8sBackend, K8sCleanupPolicy

# OpenShift
from conu.backend.origin.backend import OpenshiftBackend

# utils
from conu.utils.filesystem import Directory
from conu.utils.probes import Probe, ProbeTimeout, CountExceeded
from conu.utils import run_cmd, check_port, get_selinux_status, random_str

# exceptions
from conu.exceptions import ConuException

from conu.version import __version__ as version  # `conu.version == "3.1.4"` should work as well

# enumerations
from conu.apidefs.backend import CleanupPolicy

# PEP-396
# https://www.python.org/dev/peps/pep-0396/
__version__ = version

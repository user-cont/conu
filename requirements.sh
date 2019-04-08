#!/bin/bash

set -e

source /etc/os-release

set -x

# In Dockerfile we install Python3 packages from requirements.txt
# Here we install these rpms which are required by conu, either during testing or in runtime:
# - source-to-image, origin-clients, acl, docker, libselinux-utils: conu needs these binaries
# - pip: to have different binaries for Python3
# - pytest: to have different binaries for Python3
# - pyxattr: to not build it from source
# - devel & gcc: to compile pyxattr if requirements.txt specifies different version than we install here

# which is not installed in the base image
if [ -f /bin/dnf ]; then
    dnf install -y acl docker libselinux-utils \
        source-to-image \
        origin-clients \
        python3-pip python3-pytest \
        python3-pyxattr \
        gcc python3-devel \
        nmap-ncat \
        podman \
        skopeo
fi

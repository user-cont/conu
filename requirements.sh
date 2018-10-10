#!/bin/bash

set -e

source /etc/os-release

set -x

# In Dockerfile we install Python3 & Python2 packages from requirements.txt
# Here we install these Python rpms:
# - pip: to have different binaries for Python3 & Python2
# - pytest: to have different binaries for Python3 & Python2
# - pyxattr: to not build it from source
# - devel & gcc: to compile pyxattr if requirements.txt specifies different version than we install here

if [ "${NAME}" == "Fedora" ]; then
    dnf install -y acl docker libselinux-utils \
        source-to-image \
        origin-clients \
        python3-pip python2-pip \
        python3-pyxattr python2-pyxattr \
        python3-pytest python2-pytest \
        gcc python3-devel python2-devel \
        python2-enum34 \
        python3-requests python2-requests \
        python3-docker python2-docker \
        python3-kubernetes python2-kubernetes \
        make
fi

#!/bin/bash

set -e

source /etc/os-release

set -x

# In Dockerfile we install Python3 & Python2 packages from requirements.txt
# Here we install these Python rpms:
# - pip: to have different binaries for Python3 & Python2
# - pytest: to have different binaries for Python3 & Python2
# - pyxattr: to not build it from source

if [ "${NAME}" == "Fedora" ]; then
    dnf install -y acl docker libselinux-utils \
        source-to-image \
        origin-clients \
        python3-pip python2-pip \
        python3-pyxattr \
        python3-pytest python2-pytest \
        gcc python3-devel python2-devel \
        make

    # It has different naming in Fedora 27 and Fedora 28
    dnf install -y python2-pyxattr || dnf install -y pyxattr
fi

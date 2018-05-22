#!/bin/bash

set -e

# old s2i breaks tests & functionality
dnf install -y acl docker libselinux-utils \
  source-to-image \
  python3-pyxattr python2-pyxattr \
  python3-docker python2-docker \
  python3-six python2-six \
  python3-pip python2-pip \
  python3-pytest python2-pytest \
  python2-enum34

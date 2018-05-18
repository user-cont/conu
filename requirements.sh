#!/bin/bash

set -e

# old s2i breaks tests & functionality
dnf install -y acl docker libselinux-utils \
  https://kojipkgs.fedoraproject.org//packages/source-to-image/1.1.7/1.fc28/x86_64/source-to-image-1.1.7-1.fc28.x86_64.rpm \
  python3-pyxattr pyxattr \
  python3-docker python2-docker \
  python3-six python2-six \
  python3-pip python2-pip \
  python2-enum34

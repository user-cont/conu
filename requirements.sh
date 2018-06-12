#!/bin/bash

set -e

dnf install -y acl docker libselinux-utils \
  source-to-image \
  origin-clients \
  python3-pyxattr \
  python3-docker python2-docker \
  python3-six python2-six \
  python3-kubernetes python2-kubernetes \
  python3-pip python2-pip \
  python3-pytest python2-pytest \
  python2-enum34 \
  make

# pyxattr has different naming in Fedora 27 and Fedora 28
dnf install -y python2-pyxattr || dnf install -y pyxattr

# starts openshift cluster
SKIP_SETUP_OPENSHIFT=${SKIP_SETUP_OPENSHIFT:-false}

if [ "$SKIP_SETUP_OPENSHIFT" = false ] ; then
    systemctl start docker
    oc cluster up --skip-registry-check=true
    oc new-project conu
fi

#!/bin/bash

set -e

dnf install -y acl atomic docker source-to-image \
  python3-pyxattr pyxattr \
  python3-docker python2-docker \
  python3-six python2-six \
  python3-pip python2-pip

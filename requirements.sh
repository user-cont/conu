#!/bin/bash

set -e

dnf install -y acl atomic nmap-ncat docker \
  python3-pyxattr pyxattr \
  python3-pytest python2-pytest \
  python3-docker python2-docker \
  python3-six python2-six \
  python3-pip python2-pip

pip2 install --user -r ./test-requirements.txt
pip3 install --user -r ./test-requirements.txt

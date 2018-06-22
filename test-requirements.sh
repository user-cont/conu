#!/bin/bash

set -e

source /etc/os-release

set -x

if [ "${NAME}" == "Fedora" ]; then
    dnf install -y docker origin-clients make
elif [ "${NAME}" == "CentOS Linux" ]; then
    yum install -y centos-release-openshift-origin39
    yum install -y docker origin-clients make
fi

systemctl start docker
oc cluster status || oc cluster up --skip-registry-check=true
oc get project conu || oc new-project conu

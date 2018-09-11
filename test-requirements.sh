#!/bin/bash

set -e

source /etc/os-release

set -x

if [ "${NAME}" == "Fedora" ]; then
    dnf install -y docker origin make
elif [ "${NAME}" == "CentOS Linux" ]; then
    yum install -y docker origin make
fi

setenforce 0
systemctl start docker
touch /etc/docker/daemon.json
echo '{"insecure-registries" : [ "172.30.0.0/16" ]}' > /etc/docker/daemon.json
systemctl restart docker
oc cluster status || oc cluster up --version v3.9.0
oc login -u system:admin
oc adm policy add-role-to-user system:registry developer
oc adm policy add-role-to-user admin developer -n openshift
oc adm policy add-role-to-user system:image-builder developer
oc adm policy add-cluster-role-to-user cluster-reader developer
oc adm policy add-cluster-role-to-user admin developer
oc adm policy add-cluster-role-to-user cluster-admin developer
oc login -u developer -p developer

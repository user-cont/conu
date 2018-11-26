#!/bin/bash

set -e

source /etc/os-release

set -x

if [ "${NAME}" == "Fedora" ]; then
    # let's use cutting edge
    dnf install -y --enablerepo=updates-testing docker make podman
    dnf update -y --enablerepo=updates-testing docker podman
elif [ "${NAME}" == "CentOS Linux" ]; then
    yum install -y docker make podman
fi

setenforce 0
systemctl stop firewalld # firewall on CentOS does not allow docker login into OpenShift registry
systemctl start docker
touch /etc/docker/daemon.json
echo '{"insecure-registries" : [ "172.30.0.0/16" ]}' > /etc/docker/daemon.json
systemctl restart docker
curl -Lo openshift.tar.gz https://github.com/openshift/origin/releases/download/v3.9.0/openshift-origin-server-v3.9.0-191fece-linux-64bit.tar.gz
tar -zxf openshift.tar.gz
mv -v openshift-origin-server-v3.9.0-191fece-linux-64bit/* /sbin/
oc cluster status || oc cluster up --version v3.9.0
oc login -u system:admin
oc adm policy add-role-to-user system:registry developer
oc adm policy add-role-to-user admin developer -n openshift
oc adm policy add-role-to-user system:image-builder developer
oc adm policy add-cluster-role-to-user cluster-reader developer
oc adm policy add-cluster-role-to-user admin developer
oc adm policy add-cluster-role-to-user cluster-admin developer
oc login -u developer -p developer

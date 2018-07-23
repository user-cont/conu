#!/bin/bash

set -e

source /etc/os-release

set -x

if [ "${NAME}" == "Fedora" ]; then
    dnf install -y docker make
elif [ "${NAME}" == "CentOS Linux" ]; then
    yum install -y docker make
fi

setenforce 0
systemctl start docker
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && chmod +x minikube
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v1.10.0/bin/linux/amd64/kubectl && chmod +x kubectl && mv kubectl /usr/local/bin/


export MINIKUBE_WANTUPDATENOTIFICATION=false
export MINIKUBE_WANTREPORTERRORPROMPT=false
export MINIKUBE_HOME=$HOME
export CHANGE_MINIKUBE_NONE_USER=true
mkdir -p $HOME/.kube
touch $HOME/.kube/config

export KUBECONFIG=$HOME/.kube/config
./minikube start --vm-driver=none --extra-config=apiserver.admission-control="" --extra-config=kubelet.cgroup-driver=systemd --kubernetes-version=v1.10.0

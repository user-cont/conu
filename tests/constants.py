# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#
from __future__ import print_function, unicode_literals

FEDORA_REPOSITORY = "registry.fedoraproject.org/fedora"
FEDORA_MINIMAL_REPOSITORY = "registry.fedoraproject.org/fedora-minimal"
FEDORA_MINIMAL_REPOSITORY_TAG = "33"
FEDORA_MINIMAL_REPOSITORY_DIGEST = "registry.fedoraproject.org/fedora-minimal@" \
    "sha256:51ff92dc28e9ef4bbd6400ea1d0845c00c25149bc6902897eeb73b0ad469b7e9"
FEDORA_MINIMAL_IMAGE = "{}:{}".format(FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG)
FEDORA_RELEASE = "Fedora release 33 (Thirty Three)\n"
S2I_IMAGE = "punchbag"

THE_HELPER_IMAGE = "rudolph"


CENTOS_PYTHON_3 = "centos/python-36-centos7"
CENTOS_MARIADB_10_2 = "centos/mariadb-102-centos7"
MY_PROJECT = "myproject"
OC_CLUSTER_USER = "developer"
CENTOS_POSTGRES_9_6 = "centos/postgresql-96-centos7"
CENTOS_POSTGRES_9_6_TAG = "9.6"
DJANGO_POSTGRES_TEMPLATE = "django-psql-example"
INTERNAL_REGISTRY_URL = "172.30.1.1:5000"

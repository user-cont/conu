#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Jan Scotka <jscotka@redhat.com>
#          Petr Hracek <phracek@redhat.com>

import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def get_requirements():
    with open("./requirements.txt") as fd:
        return fd.readlines()


data_files = {}

# https://packaging.python.org/guides/single-sourcing-package-version/
version = {}
with open("./conu/version.py") as fp:
    exec(fp.read(), version)


setup(
    name='conu',
    version=version["__version__"],
    description='Container testing library',
    keywords='containers,testing',
    author='Red Hat',
    author_email='user-cont-team@redhat.com',
    url='https://github.com/fedora-modularity/conu',
    license='GPLv2+',
    packages=find_packages(exclude=['examples', 'tests', 'tests.*']),
    include_package_data=True,
    data_files=data_files.items(),
    entry_points={},
    setup_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    install_requires=get_requirements()
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT

import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def get_requirements():
    packages = []

    with open("./requirements.txt") as fd:
        for line in fd.readlines():
            if not line or line.startswith('-i'):
                continue
            packages.append(line)
    return packages


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
    url='https://github.com/user-cont/conu',
    license='MIT',
    packages=find_packages(exclude=['examples', 'tests', 'tests.*']),
    include_package_data=True,
    data_files=data_files.items(),
    entry_points={},
    setup_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    install_requires=get_requirements()
)

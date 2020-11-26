# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#

# TODO: move this line to some generic constants, instead of same in
# docker and nspawn
CONU_ARTIFACT_TAG = 'CONU.'

CONU_IMAGES_STORE = "/opt/conu-nspawn-images/"
CONU_NSPAWN_BASEPACKAGES = [
    "dnf",
    "iproute",
    "dhcp-client",
    "initscripts",
    "passwd",
    "systemd",
    "rpm",
    "bash",
    "shadow-utils",
    "sssd-client",
    "util-linux",
    "libcrypt",
    "sssd-client",
    "coreutils",
    "glibc-all-langpacks",
    "vim-minimal"]
BOOTSTRAP_IMAGE_SIZE_IN_MB = 5000
BOOTSTRAP_FS_UTIL = "mkfs.ext4"
BOOTSTRAP_PACKAGER = [
                "dnf",
                "-y",
                "install",
                "--nogpgcheck",
                "--setopt=install_weak_deps=False",
                "--allowerasing"]
DEFAULT_RETRYTIMEOUT = 30
DEFAULT_SLEEP = 1

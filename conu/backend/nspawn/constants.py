# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# TODO: move this line to some generic constants, instead of same in
# docker and nspawn
CONU_ARTIFACT_TAG = 'CONU.'

CONU_IMAGES_STORE = "/var/lib/machines"
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
BOOTSTRAP_IMAGE_SIZE_IN_MB = 100000
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

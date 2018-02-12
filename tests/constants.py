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
from __future__ import print_function, unicode_literals

FEDORA_REPOSITORY = "registry.fedoraproject.org/fedora"
FEDORA_MINIMAL_REPOSITORY = "registry.fedoraproject.org/fedora-minimal"
FEDORA_MINIMAL_REPOSITORY_TAG = "26"
FEDORA_MINIMAL_IMAGE = "{}:{}".format(FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG)
S2I_IMAGE = "punchbag"

THE_HELPER_IMAGE = "rudolph"

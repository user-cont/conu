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


from conu import DockerBackend
from conu.helpers import get_container_output


with DockerBackend() as backend:
    # This will run the container using the supplied command, collects output and
    # cleans the container
    output = get_container_output(backend, "registry.fedoraproject.org/fedora", ["ls", "-1", "/etc"],
                                  image_tag="27")
    assert "passwd" in output

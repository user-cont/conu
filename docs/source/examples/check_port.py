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

from conu import DockerBackend, DockerRunBuilder

with DockerBackend() as backend:
    image = backend.ImageClass('centos/httpd-24-centos7')
    additional_opts = ["-p", "8080:8080"]
    container = image.run_via_binary(additional_opts=additional_opts)
    container.wait_for_port(port=8080, timeout=-1)

    container.stop()
    container.delete()

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

import subprocess
import time

from conu import DockerBackend

with DockerBackend() as backend:
    image = backend.ImageClass("registry.fedoraproject.org/fedora", tag='27')
    additional_opts = ['-i', '-e', 'KEY=space']

    cont = image.run_via_binary_in_foreground(additional_opts=additional_opts, popen_params={"stdin": subprocess.PIPE})
    try:
        assert cont.is_running()
        assert cont.logs_unicode() == ""

        cont.write_to_stdin(message=b'echo $KEY\n')
        # give container time to process
        time.sleep(0.2)
        assert cont.logs_unicode() == 'space\n'
    finally:
        cont.delete(force=True)

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
import os

from conu import S2IDockerImage
from ..constants import S2I_IMAGE


def test_s2i_extending(tmpdir):
    t = str(tmpdir)
    exec_path = os.path.join(t, "secret-executable")
    secret_message = "Can I have a cup of cocoa?"
    with open(exec_path, "w") as fd:
        fd.write("""\
        #!/bin/bash
        echo "%s"
        """ % secret_message)
    os.chmod(exec_path, 0o755)
    i = S2IDockerImage(S2I_IMAGE)
    ei = i.extend(t, "extended-punchbag")
    c = ei.run_via_binary()
    c.wait()
    assert c.logs_unicode() == secret_message + '\n'


def test_s2i_usage():
    i = S2IDockerImage(S2I_IMAGE)
    assert i.usage() == """\
This is the punchbag S2I image:
To use it, install S2I: https://github.com/openshift/source-to-image

Sample invocation:

s2i build git://<source code> punchbag <application image>

You can then run the resulting image via:
docker run <application image>"""

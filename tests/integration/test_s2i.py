# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
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

# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
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

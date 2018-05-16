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

import logging
import unittest
import os

from conu.backend.null.backend import NullBackend
from conu.backend.nspawn.backend import NspawnBackend
from conu.backend.docker.backend import DockerBackend

logger = logging.getLogger(__name__)


class VariousBackends(unittest.TestCase):
    def setUp(self):
        self.back = globals()[os.environ.get("BACKEND", "NullBackend")]()
        self.repo = os.environ.get("REPOSITORY", "NOTHING_IMPORTANT")
        self.image = self.back.ImageClass(repository=self.repo)

    def test(self):
        logger.debug(self.image)
        logger.debug(self.image.get_metadata())
        self.assertTrue(self.image.get_metadata())
        self.cont = self.image.run_via_binary(command=["sleep", "10"])
        self.cont.stop()


if __name__ == '__main__':
    unittest.main()
    # call like:
    # Null:
    #   python tests/integration/test_more_backends.py
    # Nspawn:
    #   sudo REPOSITORY=https://download.fedoraproject.org/pub/fedora/linux/development/28/CloudImages/x86_64/images/Fedora-Cloud-Base-28-20180310.n.0.x86_64.raw.xz BACKEND=NspawnBackend python tests/integration/test_more_backends.py
    # Docker
    #   REPOSITORY=fedora BACKEND=DockerBackend python tests/integration/test_more_backends.py


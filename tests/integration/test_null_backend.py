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
import logging

from conu.backend.null.image import NullImage
from conu.backend.null.backend import NullBackend

logger = logging.getLogger(__name__)


def test_image():
    im1 = NullImage(repository="somename", tag="tag")
    logger.debug(im1)
    logger.debug(im1.get_metadata())
    assert "somename tag" in str(im1)
    logger.debug(im1.get_id())


def test_image_run_foreground():
    im = NullImage()
    cmd = im.run_foreground(["ls", "/"]).communicate()
    out = cmd
    assert not out[0]
    out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
    assert "sbin" in out[0]


def test_backend():
    back = NullBackend
    im = back.ImageClass()
    out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
    logger.debug(out)
    assert "sbin" in out[0]

def test_container_basic():
    im = NullImage()
    cont = im.run_via_binary(command=["sleep", "10"])
    logger.debug(im.get_metadata())
    logger.debug(cont.get_metadata())
    assert cont.is_running()
    assert cont.selfcheck()
    cont.stop()
    assert cont.selfcheck()
    assert not cont.is_running()
    cont.start()
    assert cont.selfcheck()
    assert cont.is_running()
    cont.stop()

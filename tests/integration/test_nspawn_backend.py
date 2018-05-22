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
"""
nspawn is really challenging; if you are not on btrfs, it would create a file /var/lib/machines.raw
 and mount it as /var/lib/machines; it's possible that you'll have odd limit set there, you can
 change that with `machinectl set-limit 4G`
"""
import subprocess
import logging
import os

import pytest

from conu.backend.nspawn.image import NspawnImage, ImagePullPolicy
from conu.backend.nspawn.backend import NspawnBackend
from conu.utils import mkdtemp, run_cmd


logger = logging.getLogger(__name__)
image_name = "Fedora-Cloud-Base-27-1.6.x86_64"
url = "https://download.fedoraproject.org/pub/fedora/linux/development/28/CloudImages/" \
    "x86_64/images/Fedora-Cloud-Base-28-20180310.n.0.x86_64.raw.xz"
bootstrap_repos = [
    "https://download.fedoraproject.org/pub/fedora/linux/releases/27/Workstation/x86_64/os/"
]


@pytest.mark.nspawn
class TestNspawnBackend(object):
    def test_image(self):
        im1 = NspawnImage(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                          location=url)
        logger.debug("%s", im1)
        logger.debug("%s", im1.get_metadata())
        logger.debug("%s", im1.get_id())
        logger.debug("%s", im1.get_full_name())

    def test_mounts(self):
        im = NspawnImage(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                         location=url)
        with im.mount() as fs:
            logger.debug(fs.mount_point)
            assert fs.directory_is_present("/lost+found")

    def test_image_run_foreground(self):
        im = NspawnImage(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                         location=url)
        cmd = im.run_foreground(["ls", "/"]).communicate()
        out = cmd
        assert not out[0]

        out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
        stdout = out[0].decode("utf-8")
        assert "sbin" in stdout
        # TODO: find way how to catch stderr (not possible by nspawn, everything
        # goes to stdout)
        #   nsenter could be the answer

    def test_backend(self):
        with NspawnBackend() as backend:
            im = backend.ImageClass(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                                    location=url)
            out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
            logger.debug(out)
            stdout = out[0].decode("utf-8")
            assert "sbin" in stdout
            backend.cleanup_containers()
            backend.cleanup_images()

    def test_image_bootstrapping(self):
        with NspawnBackend() as backend:
            backend.cleanup_containers()
            backend.cleanup_images()

        im = NspawnImage.bootstrap(
            repositories=bootstrap_repos,
            name="bootstrapped",
            additional_packages=["fedora-release"])
        logger.debug(im.get_metadata())
        out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
        assert "sbin" in out[0]
        out = im.run_foreground(
            ["ls", "/etc"],
            stdout=subprocess.PIPE).communicate()
        logger.info(out)
        assert "os-release" in out[0]
        out = im.run_foreground(
            ["cat", "/etc/os-release"],
            stdout=subprocess.PIPE).communicate()
        logger.info(out)
        assert "VERSION_ID=27" in out[0]
        im.rmi()

    def test_container_basic(self):
        im = NspawnImage(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                         location=url)
        cont = im.run_via_binary()
        logger.debug(im.get_metadata())
        logger.debug(cont.get_metadata())
        assert cont.is_running()
        assert cont.selfcheck()
        cont.stop()
        assert not cont.selfcheck()
        cont.start()
        assert cont.selfcheck()
        cont.stop()
        assert not cont.selfcheck()

    def test_container_exit_states(self):
        im = NspawnImage(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                         location=url)
        cont = im.run_via_binary()
        try:
            cont.execute(["exit", "1"])
        except subprocess.CalledProcessError:
            pass
        else:
            raise BaseException("It has to fail")
        cont.execute(["exit", "0"])
        cont.execute(["touch", "/aa"])
        cont.execute(["ls", "/aa"])
        assert 2 == cont.execute(["ls", "/aabb"], ignore_status=True)
        out = cont.execute(["ls", "/"], return_output=True)
        assert "sbin" in out
        out = cont.execute(["ls", "/"], return_full_dict=True)
        logger.debug(out)
        cont.stop()

    def test_volumes(self):
        im = NspawnImage(repository=image_name, pull_policy=ImagePullPolicy.IF_NOT_PRESENT,
                         location=url)
        dirname = mkdtemp()
        filename = "somefile"
        host_fn = os.path.join(dirname, filename)
        run_cmd(["touch", host_fn])
        cont = im.run_via_binary(volumes=["{}:/opt".format(dirname)])
        cont.execute(["ls", os.path.join("/opt", filename)])
        assert os.path.exists(host_fn)
        cont.execute(["rm", "-f", os.path.join("/opt", filename)])
        assert not os.path.exists(host_fn)
        os.rmdir(dirname)
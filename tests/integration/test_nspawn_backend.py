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
import os

from conu.backend.nspawn.image import NspawnImage
from conu.backend.nspawn.backend import NspawnBackend
from conu.utils import mkdtemp, run_cmd

logger = logging.getLogger(__name__)
repository = "https://download.fedoraproject.org/pub/fedora/linux/development/28/CloudImages/x86_64/images/Fedora-Cloud-Base-28-20180310.n.0.x86_64.raw.xz"
tag = "abc"
bootstrap_repos = [
    "http://ftp.fi.muni.cz/pub/linux/fedora/linux/releases/27/Workstation/x86_64/os/"]


def test_image():
    im1 = NspawnImage(repository=repository, tag=tag)
    logger.debug(im1)
    logger.debug(im1.get_metadata())
    assert "/var/lib/machines" in im1.get_metadata()["Path"]
    logger.debug(im1.get_id())
    assert tag in im1.get_id()
    logger.debug(im1.get_full_name())
    assert repository in im1.get_full_name()
    im2 = im1.tag_image("sometag")
    assert "_sometag" in im2.get_id()
    im2.rmi()
    assert im2.get_id() not in im2.list_all()
    im2.pull()
    assert im2.get_id() in im2.list_all()
    im2.rmi()
    assert im2.get_id() not in im2.list_all()


def test_mounts():
    im = NspawnImage(repository=repository, tag=tag)
    with im.mount() as fs:
        logger.debug(fs.mount_point)
        assert fs.directory_is_present("/lost+found")


def test_image_run_foreground():
    im = NspawnImage(repository=repository, tag=tag)
    cmd = im.run_foreground(["ls", "/"]).communicate()
    out = cmd
    assert not out[0]

    out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
    assert "sbin" in out[0]
    # TODO: find way how to catch stderr (not possible by nspawn, everything
    # goes to stdout)


def test_backend():
    back = NspawnBackend
    im = back.ImageClass(repository=repository, tag=tag)
    out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
    logger.debug(out)
    assert "sbin" in out[0]
    back.cleanup_containers()
    back.cleanup_images()


def test_image_bootstrapping():
    NspawnBackend.cleanup_containers()
    NspawnBackend.cleanup_images()

    im = NspawnImage.bootstrap(
        repositories=bootstrap_repos,
        additional_packages=["fedora-release"])
    logger.debug(im.get_metadata())
    out = im.run_foreground(["ls", "/"], stdout=subprocess.PIPE).communicate()
    assert "sbin" in out[0]
    out = im.run_foreground(
        ["ls", "/etc"],
        stdout=subprocess.PIPE).communicate()
    assert "os-release" in out[0]
    out = im.run_foreground(
        ["cat", "/etc/os-release"],
        stdout=subprocess.PIPE).communicate()
    assert "VERSION_ID=27" in out[0]
    im.rmi()


def test_container_basic():
    im = NspawnImage(repository=repository, tag=tag)
    cont = im.run()
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


def test_container_exit_states():
    im = NspawnImage(repository=repository, tag=tag)
    cont = im.run()
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


def test_volumes():
    im = NspawnImage(repository=repository, tag=tag)
    dirname = mkdtemp()
    filename = "somefile"
    host_fn = os.path.join(dirname, filename)
    run_cmd(["touch", host_fn])
    cont = im.run(volumes=["{}:/opt".format(dirname)])
    cont.execute(["ls", os.path.join("/opt", filename)])
    assert os.path.exists(host_fn)
    cont.execute(["rm", "-f", os.path.join("/opt", filename)])
    assert not os.path.exists(host_fn)
    os.rmdir(dirname)

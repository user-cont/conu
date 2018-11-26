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

from __future__ import print_function, unicode_literals

import errno
import logging
import os
import random
import shutil
import socket
import string
import subprocess
import tempfile

from conu.exceptions import ConuException


logger = logging.getLogger(__name__)


def convert_kv_to_dict(data):
    """
    convert text values in format:
    key1=value1
    key2=value2
    to dict {'key1':'value1', 'key2':'value2'}

    :param data: string containing lines with these values
    :return: dict
    """
    output = {}
    for line in data.split("\n"):
        stripped = line.strip()
        if stripped:
            key, value = stripped.split("=", 1)
            output[key] = value
    return output


def check_port(port, host, timeout=10):
    """
    connect to port on host and return True on success

    :param port: int, port to check
    :param host: string, host address
    :param timeout: int, number of seconds spent trying
    :return: bool
    """
    logger.info("trying to open connection to %s:%s", host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        logger.info("was connection successful? errno: %s", result)
        if result == 0:
            logger.debug('port is opened: %s:%s' % (host, port))
            return True
        else:
            logger.debug('port is closed: %s:%s' % (host, port))
            return False
    finally:
        sock.close()


def get_selinux_status():
    """
    get SELinux status of host

    :return: string, one of Enforced, Permissive, Disabled
    """
    getenforce_command_exists()
    # alternatively, we could read directly from /sys/fs/selinux/{enforce,status}, but status is
    # empty (why?) and enforce doesn't tell whether SELinux is disabled or not
    o = run_cmd(["getenforce"], return_output=True).strip()  # libselinux-utils
    logger.debug("SELinux is %r", o)
    return o


def is_selinux_disabled():
    """
    check if SELinux is disabled

    :return: bool, True if disabled, False otherwise
    """
    return get_selinux_status() == "Disabled"


def random_str(size=10):
    """
    create random string of selected size

    :param size: int, length of the string
    :return: the string
    """
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(size))


def run_cmd(cmd, return_output=False, ignore_status=False, log_output=True, **kwargs):
    """
    run provided command on host system using the same user as you invoked this code, raises
    subprocess.CalledProcessError if it fails

    :param cmd: list of str
    :param return_output: bool, return output of the command
    :param ignore_status: bool, do not fail in case nonzero return code
    :param log_output: bool, if True, log output to debug log
    :param kwargs: pass keyword arguments to subprocess.check_* functions; for more info,
            please check `help(subprocess.Popen)`
    :return: None or str
    """
    logger.debug('command: "%s"' % ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, **kwargs)
    output = process.communicate()[0]
    if log_output:
        logger.debug(output)

    if process.returncode > 0:
        if ignore_status:
            if return_output:
                return output
            else:
                return process.returncode
        else:
            raise subprocess.CalledProcessError(cmd=cmd, returncode=process.returncode)
    if return_output:
        return output


def mkstemp(dir=None):
    """
    calls tempfile.mkstemp, the temporary file is prefixed with 'conu-'

    :param dir: str, path to dir where the temporary file should be created

    :return: tuple, (fd, filename)
    """
    return tempfile.mkstemp(prefix="conu-", dir=dir)


def mkdtemp():
    """
    calls tempfile.mkdtemp, the temporary directory is prefixed with 'conu-'

    :return: str, path to the directory
    """
    return tempfile.mkdtemp(prefix="conu-")


def random_tmp_filename():
    """ generate string which can be used as a filename for temporary file """
    return "conu-" + random_str(32)


class CommandDoesNotExistException(ConuException):
    """ Requested command is not present on the system """


def command_exists(command, noop_invocation, exc_msg):
    """
    Verify that the provided command exists. Raise CommandDoesNotExistException in case of an
    error or if the command does not exist.

    :param command: str, command to check (python 3 only)
    :param noop_invocation: list of str, command to check (python 2 only)
    :param exc_msg: str, message of exception when command does not exist
    :return: bool, True if everything's all right (otherwise exception is thrown)
    """
    try:
        found = bool(shutil.which(command))  # py3 only
    except AttributeError:  # py2 branch
        try:
            p = subprocess.Popen(noop_invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            found = False
        else:
            stdout, stderr = p.communicate()
            found = p.returncode == 0
            if not found:
                logger.error("`%s` exited with a non-zero return code (%s)",
                             noop_invocation, p.returncode)
                logger.error("command stdout = %s", stdout)
                logger.error("command stderr = %s", stderr)
    if not found:
        raise CommandDoesNotExistException(exc_msg)
    return True


def s2i_command_exists():
    return command_exists(
        "s2i",
        ["s2i", "version"],
        "s2i command doesn't seem to be available on your system. Usually it's available in "
        "'source-to-image' package. For more info, please consult the upstream documentation "
        "available at 'https://github.com/openshift/source-to-image'."
    )


def oc_command_exists():
    return command_exists(
        "oc",
        ["oc", "version"],
        "oc command doesn't seem to be available on your system. Usually it's available in "
        "'origin' or 'origin-clients' package. For more info, please"
        "consult the upstream documentation available at 'https://github.com/openshift/origin'."
    )


def chcon_command_exists():
    return command_exists(
        "chcon",
        ["chcon", "--version"],
        "chcon command doesn't seem to be available on your system. Usually it's available in "
        "'coreutils' package. Please consult documentation of your operating system."
    )


def setfacl_command_exists():
    return command_exists(
        "setfacl",
        ["setfacl", "-v"],
        "setfacl command doesn't seem to be available on your system. Usually it's available in "
        "'acl' package. Please consult documentation of your operating system."
    )


def getenforce_command_exists():
    return command_exists(
        "getenforce",
        ["getenforce"],
        "getenforce command doesn't seem to be available on your system or SELinux is "
        "misconfigured. Please consult documentation of your operating system."
    )


def check_docker_command_works():
    """
    Verify that dockerd and docker binary works fine. This is performed by calling `docker
    version`, which also checks server API version.

    :return: bool, True if all is good, otherwise ConuException or CommandDoesNotExistException
              is thrown
    """
    try:
        out = subprocess.check_output(["docker", "version"],
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True)
    except OSError:
        logger.info("docker binary is not available")
        raise CommandDoesNotExistException(
            "docker command doesn't seem to be available on your system. "
            "Please install and configure docker."
        )
    except subprocess.CalledProcessError as ex:
        logger.error("exception: %s", ex)
        logger.error("rc: %s, output: %r", ex.returncode, ex.output)
        raise ConuException(
            "`docker version` call failed, it seems that your docker daemon is misconfigured or "
            "this user can't communicate with dockerd."
        )
    else:
        logger.info("docker environment info: %r", out)
    return True


def check_podman_command_works():
    """
    Verify that podman binary works fine. This is performed by calling `podman
    version`, which also checks server API version.

    :return: bool, True if all is good, otherwise ConuException or CommandDoesNotExistException
              is thrown
    """
    try:
        out = subprocess.check_output(["podman", "version"],
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True)
    except OSError:
        logger.info("podman binary is not available")
        raise CommandDoesNotExistException(
            "podman command doesn't seem to be available on your system. "
            "Please install and configure podman."
        )
    except subprocess.CalledProcessError as ex:
        logger.error("exception: %s", ex)
        logger.error("rc: %s, output: %r", ex.returncode, ex.output)
        raise ConuException(
            "`podman version` call failed, it seems that your podman is misconfigured or "
            "this user can't communicate with podman."
        )
    else:
        logger.info("podman environment info: %r", out)
    return True


def graceful_get(d, *args):
    """
    Obtain values from dicts and lists gracefully. Example:

    ::

        print(graceful_get({"a": [{1: 2}, {"b": "c"}]}, "a", "b"))
        c

    :param d: collection (usually a dict or list)
    :param args: list of keys which are used as a lookup
    :return: the value from your collection
    """
    if not d:
        return d
    value = d
    for arg in args:
        try:
            value = value[arg]
        except (IndexError, KeyError, AttributeError, TypeError) as ex:
            logger.debug("exception while getting a value %r from %s", ex, str(value)[:32])
            return None
    return value


def export_docker_container_to_directory(client, container, path):
    """
    take selected docker container, create an archive out of it and
    unpack it to a selected location

    :param client: instance of docker.APIClient
    :param container: instance of DockerContainer
    :param path: str, path to a directory, doesn't need to exist
    :return: None
    """
    # we don't do this because of a bug in docker:
    # https://bugzilla.redhat.com/show_bug.cgi?id=1570828
    # stream, _ = client.get_archive(container.get_id(), "/")
    check_docker_command_works()
    export_p = subprocess.Popen(
        ["docker", "export", container.get_id()],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    try:
        os.mkdir(path, 0o0700)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            logger.debug("mount point %s exists already", path)
        else:
            logger.error("mount point %s can't be created: %s", path, ex)
            raise
    logger.debug("about to untar the image")
    # we can't use tarfile because of --no-same-owner: files in containers are owned
    # by root and tarfile is trying to `chown 0 file` when running as an unpriv user
    p = subprocess.Popen(
        ["tar", "--no-same-owner", "-C", path, "-x"],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    while True:
        data = export_p.stdout.read(1048576)
        if not data:
            break
        p.stdin.write(data)
    p.stdin.close()
    p.wait()
    export_p.wait()
    if export_p.returncode:
        logger.error(export_p.stderr.read())
        raise ConuException("Failed to get rootfs of %s from docker." % container)
    if p.returncode:
        logger.error(p.stderr.read())
        raise ConuException("Failed to unpack the archive.")

    logger.debug("image is unpacked")


def get_oc_api_token():
    """
    Get token of user logged in OpenShift cluster
    :return: str, API token
    """
    oc_command_exists()

    try:
        return run_cmd(["oc", "whoami", "-t"], return_output=True).rstrip()  # remove '\n'
    except subprocess.CalledProcessError as ex:
        raise ConuException("oc whoami -t failed: %s" % ex)


def is_oc_cluster_running():
    """
    Check status of OpenShift cluster
    :return: bool, True if cluster is running otherwise False
    """
    try:
        run_cmd(["oc", "cluster", "status"])
        return True
    except subprocess.CalledProcessError:
        return False


def are_we_root():
    """
    is uid of current process 0?

    :return: True if root, else otherwise
    """
    return os.geteuid() == 0

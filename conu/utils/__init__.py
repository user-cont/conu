# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import logging
import random
import socket
import string
import subprocess


logger = logging.getLogger(__name__)


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


def run_cmd(cmd, return_output=False, **kwargs):
    """
    run provided command on host system using the same user as you invoked this code, raises
    subprocess.CalledProcessError if it fails

    :param cmd: list of str
    :param return_output: bool, return output of the command
    :param kwargs: pass keyword arguments to subprocess.check_* functions; for more info,
            please check `help(subprocess.Popen)`
    :return: None or str
    """
    logger.debug("command: %s" % cmd)
    if return_output:
        return subprocess.check_output(cmd, **kwargs).decode("utf-8")
    else:
        subprocess.check_call(cmd, **kwargs)

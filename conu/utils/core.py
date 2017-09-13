# -*- coding: utf-8 -*-

import string
import random
import logging
import subprocess
import os
import tempfile
import shutil
import socket
import time

logger = logging
logger.basicConfig(format='%(levelname)s: Docker : %(message)s', level=logging.DEBUG)


def run_cmd(cmd, raw=False, **kwargs):
    if not raw:
        logger.debug("Command: %s" % cmd)
        if isinstance(cmd, str):
            output = subprocess.check_output(cmd.split(" "), **kwargs)
        else:
            output = subprocess.check_output(cmd, **kwargs)
    else:
        logger.debug("Command (raw): %s" % cmd)
        output = subprocess.Popen(cmd, **kwargs)
    return output


def random_str():
    random_size = 10
    return ''.join(random.choice(string.ascii_lowercase)
                   for _ in range(random_size))


class Volume(object):
    target = None

    def __init__(self, directory=None, target=None, permissions=None,
                 facl=None, selinux_type=None, force_selinux=False):
        self.target = target
        self.force_selinux = force_selinux
        if directory:
            self.directory = directory
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
        else:
            self.directory = tempfile.mkdtemp()
        if permissions:
            self.set_permission(permissions)
        if facl:
            self.set_facl(facl)
        if selinux_type:
            self.set_selinux(selinux_type)
        logger.debug("Volume directory: %s" % self.directory)

    def set_target(self, target):
        self.target = target

    def set_selinux(self, selinux_type):
        run_cmd(["chcon", "-t", selinux_type, self.directory])

    def set_force_selinux(self, value):
        self.force_selinux = value

    def set_permission(self, perms):
        run_cmd(["chmod", perms, self.directory])

    def set_facl(self, rules):
        for rule in rules:
            run_cmd(["setfacl", "-m", rule, self.directory])

    def clean(self):
        shutil.rmtree(self.directory)

    def __str__(self):
        return self.directory

    def get_source(self):
        return self.directory

    def get_target(self):
        return self.target

    def get_force_selinux(self):
        return self.force_selinux

    def docker(self):
        if not self.target:
            raise BaseException("target not set for docker")
        output = "-v %s:%s" % (self.directory, self.target)
        if self.force_selinux:
            output += ":Z"
        return output

    def raw(self):
        return self.directory, self.target


class Probe(object):
    def check_port(self, port, host="127.0.0.1", timeout=2):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        if result == 0:
            logger.debug('port OPENed: %s:%s' % (host, port))
            return True
        else:
            logger.debug('port CLOSEDed: %s:%s' % (host, port))
            return False

    def check_file(self, path):
        return os.path.exists(path)

    def wait_cnt(self, count=1, sleep=1, fnc=bool, *args, **kwargs):
        for cnt in xrange(count):
            logger.debug("\tCounter: %s/%s" % (cnt, count))
            output = fnc(*args, **kwargs)
            if output:
                return True
            time.sleep(sleep)
        raise BaseException("\tCounter exceeded")

    def wait_inet_port(self, host, port, count=1, sleep=1):
        return self.wait_cnt(count=count, sleep=sleep, function=self.check_port, host=host, port=port)

    def wait_file_exist(self, path, count=1, sleep=1):
        return self.wait_cnt(count=count, sleep=sleep, function=self.check_file, path=path)

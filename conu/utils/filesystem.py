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

import logging
import os
import shutil
import pwd

from conu.exceptions import ConuException
from conu.utils import run_cmd, is_selinux_disabled, setfacl_command_exists, chcon_command_exists

import six


logger = logging.getLogger(__name__)


class Directory(object):
    """
    This class allows you to do advanced operations on filesystem directories, think of it
    as mkdir on steroids.

    We advise you to use it as a context manager:

    ::

        with Directory("/funky/path", mode=0o0700) as directory:
            path = os.path.join(directory.path, "my-dir")

    The directory is being removed once leaving the context. You can also easily do it on your own:

    ::

        directory = Directory("/funky/path", mode=0o0700)
        try:
            directory.initialize()
        finally:
            directory.clean()

    This class utilizes CLI tools to perform some operations. If some of them is missing, the
    exception is raised.
    """
    def __init__(self, path, mode=None, user_owner=None, group_owner=None, facl_rules=None,
                 selinux_context=None, selinux_user=None,
                 selinux_role=None, selinux_type=None, selinux_range=None):
        """
        For more info on SELinux, please see `$ man chcon`. An exception will be thrown if
        selinux_context is specified and at least one of other SELinux fields.

        :param path: str, path to the directory we will operate on
        :param mode: int, octal representation of permission bits, e.g. 0o0400
        :param user_owner: str or int, uid or username to own the directory
        :param group_owner: str or int, gid or group name to own the directory
        :param facl_rules: list of str, file ACLs to apply, e.g. "u:26:rwx"
        :param selinux_context: str, set directory to this SELinux context (this is the full
                context with all the field, example: "system_u:object_r:unlabeled_t:s0")
        :param selinux_user: str, user in the target security context, e.g. "system_u"
        :param selinux_role: str, role in the target security context, e.g. "object_r"
        :param selinux_type: str, type in the target security context, e.g. "unlabeled_t"
        :param selinux_range: str, range in the target security context, e.g. "s0"
        """
        if selinux_context and any([selinux_user, selinux_role, selinux_type, selinux_range]):
            raise ConuException("Don't specify both selinux_context and some of its fields.")
        if any([selinux_context, selinux_user, selinux_role, selinux_type, selinux_range]):
            if is_selinux_disabled():
                raise ConuException("You are trying to apply SELinux labels, but SELinux is "
                                    "disabled on this system. Please enable it first.")

        # if set to True, it means the directory is created and set up
        self._initialized = False

        # TODO: if path is None, we could do mkdtemp
        self.path = path
        self.mode = mode
        self.selinux_context = selinux_context
        self.selinux_user = selinux_user
        self.selinux_role = selinux_role
        self.selinux_type = selinux_type
        self.selinux_range = selinux_range
        self.facl_rules = facl_rules

        # os.chown wants int
        if isinstance(user_owner, six.string_types):
            try:
                self.owner = pwd.getpwnam(user_owner)[2]
            except KeyError as ex:
                raise ConuException("User %r not found, error message: %r" % (user_owner, ex))
        else:
            self.owner = user_owner
        if isinstance(group_owner, six.string_types):
            try:
                self.group = pwd.getpwnam(group_owner)[3]
            except KeyError as ex:
                raise ConuException("Group %r not found, error message: %r" % (group_owner, ex))
        else:
            self.group = group_owner
        # make this thing last so that all the variables are initialized

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clean()

    def clean(self):
        """
        remove the directory we operated on

        :return: None
        """
        if self._initialized:
            logger.info("brace yourselves, removing %r", self.path)
            shutil.rmtree(self.path)

    def initialize(self):
        """
        create the directory if needed and configure it

        :return: None
        """
        if not self._initialized:
            logger.info("initializing %r", self)
            if not os.path.exists(self.path):
                if self.mode is not None:
                    os.makedirs(self.path, mode=self.mode)
                else:
                    os.makedirs(self.path)
            self._set_mode()
            self._add_facl_rules()
            self._set_selinux_context()
            self._set_ownership()
            self._initialized = True
            logger.info("initialized")
            return
        logger.info("%r was already initialized", self)

    def _set_selinux_context(self):
        """
        Set SELinux context or fields using chcon program. Raises CommandDoesNotExistException
        if the command is not present on the system.

        :return: None
        """
        chcon_command_exists()
        # FIXME: do this using python API if possible
        if self.selinux_context:
            logger.debug("setting SELinux context of %s to %s", self.path, self.selinux_context)
            run_cmd(["chcon", self.selinux_context, self.path])
        if any([self.selinux_user, self.selinux_role, self.selinux_type, self.selinux_range]):
            logger.debug("setting SELinux fields of %s", self.path, self.selinux_context)
            # chcon [OPTION]... [-u USER] [-r ROLE] [-l RANGE] [-t TYPE] FILE...
            pairs = [("-u", self.selinux_user), ("-r", self.selinux_role),
                     ("-l", self.selinux_range), ("-t", self.selinux_type)]
            c = ["chcon"]
            for p in pairs:
                if p[1]:
                    c += p
            c += [self.path]
            run_cmd(c)

    def _set_ownership(self):
        """
        set ownership of the directory: user and group

        :return: None
        """
        if self.owner or self.group:
            args = (
                self.path,
                self.owner if self.owner else -1,
                self.group if self.group else -1,
            )
            logger.debug("changing ownership bits of %s to %s", self.path, args)
            os.chown(*args)

    def _set_mode(self):
        """
        set permission bits if needed using python API os.chmod

        :return: None
        """
        if self.mode is not None:
            logger.debug("changing permission bits of %s to %s", self.path, oct(self.mode))
            os.chmod(self.path, self.mode)

    def _add_facl_rules(self):
        """
        Apply ACL rules on the directory using setfacl program. Raises CommandDoesNotExistException
        if the command is not present on the system.

        :return: None
        """
        setfacl_command_exists()
        # we are not using pylibacl b/c it's only for python 2
        if self.facl_rules:
            logger.debug("adding ACLs %s to %s", self.facl_rules, self.path)
            r = ",".join(self.facl_rules)
            run_cmd(["setfacl", "-m", r, self.path])

    def __repr__(self):
        return "Directory(path=%s)" % (self.path, )

    def __unicode__(self):
        return str(self.path)

    def __str__(self):
        # we could be possible initialize here, but... it's tricky
        return str(self.path)


class Volume(object):
    """
    The representation of container volume.
    """

    def __init__(self, target, source=None, mode=None):
        if source and not isinstance(source, Directory):
            self.source = Directory(path=source)
        else:
            self.source = source
        self.target = target
        self.mode = mode

    def __str__(self):
        """
        Cmd option representing the volume
        :return:
        """
        result = self.target
        if self.source:
            result = "{}:{}".format(self.source.path, result)
        if self.mode:
            result = "{}:{}".format(result, self.mode)
        return result

    @classmethod
    def create_from_tuple(cls, volume):
        """
        Create instance from tuple.
        :param volume: tuple in one one of the following forms: target | source,target | source,target,mode
        :return: instance of Volume
        """
        if isinstance(volume, six.string_types):
            return Volume(target=volume)
        elif len(volume) == 2:
            return Volume(source=volume[0],
                          target=volume[1])
        elif len(volume) == 3:
            return Volume(source=volume[0],
                          target=volume[1],
                          mode=volume[2])
        else:
            logger.debug("Cannot create volume instance from {}."
                         "It has to be tuple of form target x source,target x source,target,mode.".format(volume))
            raise ConuException("Cannot create volume instance.")

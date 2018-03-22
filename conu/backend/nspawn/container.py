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
Implementation of a nspawn container
"""

import logging
import subprocess
import time
from copy import deepcopy

from conu.apidefs.container import Container
from conu.exceptions import ConuException
from conu.utils import run_cmd, random_str, convert_kv_to_dict, command_exists
import constants


logger = logging.getLogger(__name__)


class NspawnContainer(Container):

    def __init__(self, image, container_id, name=None,
                 popen_instance=None, start_process=None, start_action=None):
        """
        Utilities usable for containers

        :param image: image to use (instance of Image class)
        :param container_id: id of running container (created by Image.run method)
        :param name: optional name of container
        :param popen_instance: not used anyhow now
        :param start_process: subporocess instance with start process
        :param start_action: set with 4 parameters for starting container
        """
        # This is important to indentify if systemd supports --wait option,
        # RHEL7 does not support --wait
        self.systemd_wait_support = None
        # TODO: this is example how it can be named, and it could be used as callback method from parent class
        self.system_requirements()
        # TODO: find way how to find image for already running container, it is
        # not simple, not shown by list, status, or other commands
        super(NspawnContainer, self).__init__(image, container_id, name)
        if not name:
            self.name = self._id
        self.popen_instance = popen_instance
        self.start_process = start_process
        self.start_action = start_action

    @staticmethod
    def system_requirements():
        """
        Check if all necessary packages are installed on system

        :return: None or raise exception if some tooling is missing
        """
        command_exists("systemd-run",
            ["systemd-run", "--help"],
            "Command systemd-run does not seems to be present on your system"
            "Do you have system with systemd")
        command_exists(
            "machinectl",
            ["machinectl", "--help"],
            "Command machinectl does not seems to be present on your system"
            "Do you have system with systemd")

    def __repr__(self):
        # TODO: very similar to Docker method, move to API, this is the proper
        # way
        return "%s(image=%s, id=%s)" % (
            self.__class__, self.image, self.get_id())

    def __str__(self):
        # TODO: move to API
        return self.get_id()

    def start(self):
        self.start_process = NspawnContainer.internal_run_container(name=self.name, callback_method=self.start_action)
        return self.start_process

    def get_id(self):
        """
        get identifier of container
        :return: str
        """
        return self._id

    def inspect(self, refresh=True):
        """
        return cached metadata by default (a convenience method)

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        # TODO: move to API defs
        return self.get_metadata(refresh=refresh)

    def get_metadata(self, refresh=True):
        """
        return cached metadata by default

        :param refresh: bool, returns up to date metadata if set to True
        :return: dict
        """
        if refresh or not self._metadata:
            ident = self._id or self.name
            if not ident:
                raise ConuException(
                    "This container does not have a valid identifier.")
            out = run_cmd(["machinectl", "show", ident], return_output=True, ignore_status=True)
            if "Could not get path to machine" in out:
                self._metadata = {}
            else:
                self._metadata = convert_kv_to_dict(out)
        return self._metadata

    def is_running(self):
        """
        return bool in case container is running

        :return: bool
        """
        return "running" == self.get_metadata(refresh=True).get("State")

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["machinectl", "copy-to", self.get_id(), src, dest]
        run_cmd(cmd)

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container or image to host system.

        :param src: str, path to a file or a directory within container or image
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["machinectl", "copy-from", self.get_id(), src, dest]
        run_cmd(cmd)

    def stop(self):
        """
        stop this container

        :return: None
        """
        run_cmd(["machinectl", "poweroff", self.get_id()])
        self._wait_until_machine_finish()

    def kill(self, signal=None):
        """
        terminate container
        TODO: would be possible to use specific signal for terminating

        :param signal: not used now
        :return:
        """
        run_cmd(["machinectl", "terminate", self.get_id()])
        self._wait_until_machine_finish()

    def _wait_until_machine_finish(self):
        """
        Internal method
        wait until machine finish and kill main process (booted)

        :return: None
        """
        self.image._wait_for_machine_finish(self.get_id())
        # kill main run process
        self.start_process.kill()
        # TODO: there are some backgroud processes, dbus async events or something similar, there is better to wait
        # to provide enough time to finish also some async ops
        time.sleep(constants.DEFAULT_SLEEP)

    def delete(self, force=False, volumes=False):
        """
        delete underlying image

        :param force: bool - force delete, do not care about errors
        :param volumes: not used anyhow
        :return: None
        """
        try:
            self.image.rmi()
        except ConuException as ime:
            if not force:
                raise ime
            else:
                pass

    def cleanup(self, force=False, delete=False):
        """
        Stop container and delete image if given param delete

        :param force: bool, force stop and delete, no errors raised
        :param delete: delete images
        :return: None
        """
        # TODO: this method could be part of API, like:
        try:
            self.stop()
        except subprocess.CalledProcessError as stop:
            logger.debug("unable to stop container via stop", stop)
            if not force:
                raise stop
            try:
                self.kill()
            except subprocess.CalledProcessError as kill:
                logger.debug("unable to stop container via kill", kill)
                pass
        if delete:
            self.delete(force=force)

    def execute(self, command, **kwargs):
        """
        Execute command inside container, it hides what method will be used

        :param command: str
        :param kwargs: pass thru to avocado.process.run command
        :return: process object
        """
        # This can lead to more actions, originally it used also "machinectl
        # shell"
        return self.run_systemdrun(deepcopy(command), **kwargs)

    def _run_systemdrun_decide(self):
        """
        Internal method
        decide if it is possible to use --wait option to systemd
        for example RHEL7 does not support --wait option

        :return: bool
        """
        if self.systemd_wait_support is None:
            self.systemd_wait_support = "--wait" in run_cmd(
                ["systemd-run", "--help"], return_output=True)
        return self.systemd_wait_support

    def _systemctl_wait_until_finish(self, machine, unit):
        """
        Internal method
        workaround for systemd-run without --wait option
        see  _run_systemdrun_decide method

        :param machine:
        :param unit:
        :return:
        """
        while True:
            metadata = convert_kv_to_dict(
                run_cmd(
                    ["systemctl", "show", "-M", machine, unit],
                    return_output=True))
            if not metadata["SubState"] in ["exited", "failed"]:
                time.sleep(0.1)
            else:
                break
        run_cmd(["systemctl", "-M", machine, "stop", unit], ignore_status=True)
        return metadata["ExecMainStatus"]

    def run_systemdrun(
            self, command, internal_background=False, return_full_dict=False,
            **kwargs):
        """
        execute command via systemd-run inside container

        :param command: list of command params
        :param internal_background: not used now
        :param kwargs: pass params to subprocess
        :return: dict with result
        """
        internalkw = deepcopy(kwargs) or {}
        original_ignore_st = internalkw.get("ignore_status", False)
        original_return_st = internalkw.get("return_output", False)
        internalkw["ignore_status"] = True
        internalkw["return_output"] = False
        unit_name = constants.CONU_ARTIFACT_TAG + "unit_" + random_str()
        opts = ["-M", self.get_id(), "--unit", unit_name]
        lpath = "/var/tmp/{}".format(unit_name)
        comout = {}
        if self._run_systemdrun_decide():
            add_wait_var = "--wait"
        else:
            # keep service exist after it finish, to be able to read exit code
            add_wait_var = "-r"
        if internal_background:
            add_wait_var = ""
        if add_wait_var:
            opts.append(add_wait_var)
        # TODO: behave move similar to run_cmd function, unable to work with clean subprocess objects because systemd-run
        # does not support return stderr, stdout, and return code directly
        # find way how to do this in better way, machinectl shell is not possible
        # https://github.com/systemd/systemd/issues/5879
        # https://github.com/systemd/systemd/issues/5878
        bashworkaround = [
            "/bin/bash",
            "-c",
            "({comm})>{path}.stdout 2>{path}.stderr".format(
                comm=" ".join(command),
                path=lpath)]
        whole_cmd = ["systemd-run"] + opts + bashworkaround
        comout['command'] = command
        comout['return_code'] = run_cmd(whole_cmd, **internalkw) or 0
        if not internal_background:
            if not self._run_systemdrun_decide():
                comout['return_code'] = self._systemctl_wait_until_finish(
                    self.name, unit_name)
            if self.is_running():
                self.copy_from(
                    "{pin}.stdout".format(
                        pin=lpath), "{pin}.stdout".format(
                        pin=lpath))
                with open("{pin}.stdout".format(pin=lpath)) as f:
                    comout['stdout'] = f.read()
                self.copy_from(
                    "{pin}.stderr".format(
                        pin=lpath), "{pin}.stderr".format(
                        pin=lpath))
                with open("{pin}.stderr".format(pin=lpath)) as f:
                    comout['stderr'] = f.read()
            logger.debug(comout)
        if not original_ignore_st and comout['return_code'] != 0:
            raise subprocess.CalledProcessError(comout['command'], comout)
        if return_full_dict:
            return comout
        if original_return_st:
            return comout['stdout']
        else:
            return comout['return_code']

    def selfcheck(self):
        """
        Test if default command will pass, it is more important for nspawn, because it happens that
        it does not returns anything

        :return: bool
        """
        # TODO: does that make sense to have this method as part of api, som
        # selfcheck, what has to pass and part of start action
        return self.execute(["true"], ignore_status=True) == 0

    def mount(self, mount_point=None):
        """
        mount filesystem inside, container (image)

        :param mount_point: str, where to mount
        :return: NspawnImageFS instance
        """
        return self.image.mount(mount_point=mount_point)

    @staticmethod
    def list_all():
        """
        list all artifacts created by CONU

        :return: dict of names
        """
        # TODO: method could be part of API
        data = run_cmd(["machinectl", "list"], return_output=True)
        output = []
        for line in data.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(
                    "MACHINE") or "No machines" in line or "machines listed" in line:
                continue
            if " systemd-nspawn " in line and constants.CONU_ARTIFACT_TAG in line:
                output.append(stripped.split(" ", 1))
        return output

    @staticmethod
    def get_backend_image(cont):
        """
        return backend image for running container

        :param cont: str - container name
        :return: NspanwImage instance
        """
        # TODO: connected with TODO in backend class
        raise NotImplemented("we have to find way how to do this op")

    @staticmethod
    def _wait_for_machine_booted(name, suffictinet_texts=None):
        """
        Internal method
        wait until machine is ready, in common case means there is running systemd-logind

        :param name: str with machine name
        :param suffictinet_texts: alternative text to check in output
        :return: True or exception
        """
        # TODO: rewrite it using probes module in utils
        suffictinet_texts = suffictinet_texts or ["systemd-logind"]
        # optionally use: "Unit: machine"
        for foo in range(constants.DEFAULT_RETRYTIMEOUT):
            time.sleep(constants.DEFAULT_SLEEP)
            out = run_cmd(
                ["machinectl", "status", name],
                ignore_status=True, return_output=True)
            for restr in suffictinet_texts:
                if restr in out:
                    time.sleep(constants.DEFAULT_SLEEP)
                    return True
        raise ConuException(
            "Unable to start machine %s within %d" %
            (name, constants.DEFAULT_RETRYTIMEOUT))

    @staticmethod
    def internal_run_container(name, callback_method, foreground=False):
        """
        Internal method what runs container process

        :param name: str - name of container
        :param callback_method: list - how to invoke container
        :param foreground: bool run in background by default
        :return: suprocess instance
        """
        logger.info("Stating machine {}".format(name))
        container_process = callback_method[0](callback_method[1], *callback_method[2], **callback_method[3])
        if not foreground:
            # wait until machine is booted when running at background, unable to execute commands without logind
            # in running container
            NspawnContainer._wait_for_machine_booted(name)
        logger.info("machine: %s starting finished" % name)
        return container_process

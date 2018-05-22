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
from conu.backend.nspawn import constants


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
        :param start_process: subprocess instance with start process
        :param start_action: set with 4 parameters for starting container
        """
        # This is important to identify if systemd supports --wait option,
        # RHEL7 does not support --wait
        self.systemd_wait_support = None
        # TODO: this is example how it can be named, and it could be used as callback method from parent class
        self.system_requirements()
        # TODO: find way how to find image for already running container, it is
        # not simple, not shown by list, status, or other commands
        super(NspawnContainer, self).__init__(image, container_id, name)
        self.popen_instance = popen_instance
        self.start_process = start_process
        self.start_action = start_action

    @staticmethod
    def machined_restart():
        """
        Workaround for systemd when machined is blocked on D-bus

        :return: int: return code
        """
        logger.debug("restart systemd-machined")
        return run_cmd("systemctl restart systemd-machined", ignore_status=True)

    @staticmethod
    def system_requirements():
        """
        Check if all necessary packages are installed on system

        :return: None or raise exception if some tooling is missing
        """
        command_exists("systemd-run",
            ["systemd-run", "--help"],
            "Command systemd-run does not seems to be present on your system. "
            "Do you have system with systemd?")
        command_exists(
            "machinectl",
            ["machinectl", "--no-pager", "--help"],
            "Command machinectl does not seems to be present on your system. "
            "Do you have system with systemd?")

    def __repr__(self):
        # TODO: very similar to Docker method, move to API, this is the proper
        # way
        return "%s(image=%s, name=%s)" % (
            self.__class__, self.image, self.name)

    def __str__(self):
        # TODO: move to API
        return self.name

    def start(self):
        self.start_process = NspawnContainer.internal_run_container(
            name=self.name, callback_method=self.start_action)
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
            out = run_cmd(["machinectl", "--no-pager", "show", ident], return_output=True, ignore_status=True)
            if "Could not get path to machine" in out:
                self._metadata = {}
            else:
                self._metadata = convert_kv_to_dict(out)
        return self._metadata

    def is_running(self):
        """
        return True when container is running, otherwise return False

        :return: bool
        """
        cmd = ["machinectl", "--no-pager", "status", self.name]
        try:
            subprocess.check_call(cmd)
            return True
        except subprocess.CalledProcessError as ex:
            logger.info("nspawn container %s is not running probably: %s",
                        self.name, ex.output)
            return False

    def copy_to(self, src, dest):
        """
        copy a file or a directory from host system to a container

        :param src: str, path to a file or a directory on host system
        :param dest: str, path to a file or a directory within container
        :return: None
        """
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["machinectl", "--no-pager", "copy-to", self.name, src, dest]
        run_cmd(cmd)

    def copy_from(self, src, dest):
        """
        copy a file or a directory from container or image to host system.

        :param src: str, path to a file or a directory within container or image
        :param dest: str, path to a file or a directory on host system
        :return: None
        """
        logger.debug("copying %s from host to container at %s", src, dest)
        cmd = ["machinectl", "--no-pager", "copy-from", self.name, src, dest]
        run_cmd(cmd)

    def stop(self):
        """
        stop this container

        :return: None
        """
        run_cmd(["machinectl", "--no-pager", "poweroff", self.name])
        self._wait_until_machine_finish()

    def kill(self, signal=None):
        """
        terminate container
        TODO: would be possible to use specific signal for terminating

        :param signal: not used now
        :return:
        """
        run_cmd(["machinectl", "--no-pager", "terminate", self.name])
        self._wait_until_machine_finish()

    def _wait_until_machine_finish(self):
        """
        Internal method
        wait until machine finish and kill main process (booted)

        :return: None
        """
        self.image._wait_for_machine_finish(self.name)
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
                    ["systemctl", "--no-pager", "show", "-M", machine, unit],
                    return_output=True))
            if not metadata["SubState"] in ["exited", "failed"]:
                time.sleep(0.1)
            else:
                break
        run_cmd(["systemctl", "--no-pager", "-M", machine, "stop", unit], ignore_status=True)
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
        opts = ["-M", self.name, "--unit", unit_name]
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
                ["machinectl", "--no-pager", "status", name],
                ignore_status=True, return_output=True)
            for restr in suffictinet_texts:
                if restr in out:
                    time.sleep(constants.DEFAULT_SLEEP)
                    return True
        raise ConuException(
            "Unable to start machine %s within %d (machinectl status command dos not contain %s)" %
            (name, constants.DEFAULT_RETRYTIMEOUT, suffictinet_texts))

    @staticmethod
    def _internal_reschedule(callback, retry=3, sleep_time=constants.DEFAULT_SLEEP):
        """
        workaround method for internal_run_container method
        It sometimes fails because of Dbus or whatever, so try to start it moretimes

        :param callback: callback method list
        :param retry: how many times try to invoke command
        :param sleep_time: how long wait before subprocess.poll() to find if it failed
        :return: subprocess object
        """
        for foo in range(retry):
            container_process = callback[0](callback[1], *callback[2], **callback[3])
            time.sleep(sleep_time)
            container_process.poll()
            rcode = container_process.returncode
            if rcode is None:
                return container_process
        raise ConuException("Unable to start nspawn container - process failed for {}-times".format(retry))


    @staticmethod
    def internal_run_container(name, callback_method, foreground=False):
        """
        Internal method what runs container process

        :param name: str - name of container
        :param callback_method: list - how to invoke container
        :param foreground: bool run in background by default
        :return: suprocess instance
        """
        if not foreground:
            logger.info("Stating machine (boot nspawn container) {}".format(name))
            # wait until machine is booted when running at background, unable to execute commands without logind
            # in running container
            nspawn_process = NspawnContainer._internal_reschedule(callback_method)
            NspawnContainer._wait_for_machine_booted(name)
            logger.info("machine: %s starting finished" % name)
            return nspawn_process
        else:
            logger.info("Stating machine (return process) {}".format(name))
            return callback_method[0](callback_method[1], *callback_method[2], **callback_method[3])
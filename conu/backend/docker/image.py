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
Utilities related to manipulate docker images.
"""
from __future__ import print_function, unicode_literals

import logging
import os
import shutil
import subprocess
import enum
from tempfile import mkdtemp

import six

from kubernetes.client.rest import ApiException

from conu.apidefs.metadata import ImageMetadata
from conu.apidefs.backend import get_backend_tmpdir
from conu.apidefs.filesystem import Filesystem
from conu.apidefs.image import Image, S2Image
from conu.backend.docker.client import get_client
from conu.backend.docker.container import DockerContainer, DockerRunBuilder
from conu.backend.docker.container_parameters import DockerContainerParameters
from conu.backend.docker.utils import inspect_to_metadata
from conu.exceptions import ConuException
from conu.utils import run_cmd, random_tmp_filename, s2i_command_exists, \
    graceful_get, export_docker_container_to_directory
from conu.utils.filesystem import Volume
from conu.utils.probes import Probe
from conu.utils.rpms import check_signatures
from conu.backend.k8s.pod import Pod
from conu.backend.k8s.client import get_core_api

import docker.errors

logger = logging.getLogger(__name__)


class DockerImageViaArchiveFS(Filesystem):
    def __init__(self, image, mount_point=None):
        """
        Provide image as an archive

        :param image: instance of DockerImage
        :param mount_point: str, directory where the filesystem will be made available
        """
        super(DockerImageViaArchiveFS, self).__init__(image, mount_point=mount_point)
        self.image = image

    @property
    def mount_point(self):
        if self._mount_point is None:
            # we pick /var/tmp b/c it's not on tmpfs
            self._mount_point = mkdtemp(prefix="conu", dir="/var/tmp")
            self.mount_point_provided = False
        return self._mount_point

    def __enter__(self):
        client = get_client()
        c = client.create_container(self.image.get_id())
        container = DockerContainer(self.image, c["Id"])
        try:
            export_docker_container_to_directory(client, container, self.mount_point)
        finally:
            container.delete(force=True)
        return super(DockerImageViaArchiveFS, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.mount_point_provided:
            # some dirs are 0400
            run_cmd(["chmod", "-R", "u+w", self.mount_point])
            shutil.rmtree(self.mount_point)


class DockerImagePullPolicy(enum.Enum):
    """
    This Enum defines the policy for pulling the docker images. The pull operation happens when
    creating an instance of a docker image. Supported values:

    * NEVER - do not pull the image
    * IF_NOT_PRESENT - pull it only if the image is not present
    * ALWAYS - always initiate the pull process - the image is being pulled even if it's present
      locally. It means that it may be overwritten by a remote counterpart or there may
      be a exception being raised if no such image is present in the registry.
    """
    NEVER = 0
    IF_NOT_PRESENT = 1
    ALWAYS = 2


class DockerImage(Image):
    """
    Utility functions for docker images.
    """

    def __init__(self, repository, tag="latest", identifier=None,
                 pull_policy=DockerImagePullPolicy.IF_NOT_PRESENT):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        :param identifier: str, unique identifier for this image
        :param pull_policy: enum, strategy to apply for pulling the image
        """
        super(DockerImage, self).__init__(repository, tag=tag)
        if not isinstance(tag, (six.string_types, None.__class__)):
            raise ConuException("'tag' is not a string type")
        if not isinstance(pull_policy, DockerImagePullPolicy):
            raise ConuException("'pull_policy' is not an instance of DockerImagePullPolicy")
        if identifier:
            self._id = identifier
        self.d = get_client()
        self.pull_policy = pull_policy

        self._inspect_data = None
        self.metadata = ImageMetadata()

        if self.pull_policy == DockerImagePullPolicy.ALWAYS:
            logger.debug("pull policy set to 'always', pulling the image")
            self.pull()
        elif self.pull_policy == DockerImagePullPolicy.IF_NOT_PRESENT and not self.is_present():
            logger.debug("pull policy set to 'if_not_present' and image is not present, "
                         "pulling the image")
            self.pull()
        elif self.pull_policy == DockerImagePullPolicy.NEVER:
            logger.debug("pull policy set to 'never'")

    def __repr__(self):
        return "DockerImage(repository=%s, tag=%s)" % (self.name, self.tag)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Provide full, complete image name

        :return: str
        """
        return "%s:%s" % (self.name, self.tag)

    def get_id(self):
        """
        get unique identifier of this image

        :return: str
        """
        if self._id is None:
            self._id = self.inspect(refresh=False)["Id"]
        return self._id

    def is_present(self):
        """
        Is this docker image present locally on the system?

        :return: bool, True if it is, False if it's not
        """
        # TODO: move this method to generic API
        try:
            return bool(self.inspect())
        except docker.errors.DockerException:
            return False

    def pull(self):
        """
        Pull this image from registry. Raises an exception if the image is not found in
        the registry.

        :return: None
        """
        for json_e in self.d.pull(repository=self.name, tag=self.tag, stream=True, decode=True):
            logger.debug(json_e)
            status = graceful_get(json_e, "status")
            if status:
                logger.info(status)
            else:
                error = graceful_get(json_e, "error")
                logger.error(status)
                raise ConuException("There was an error while pulling the image %s: %s",
                                    self.name, error)

    def push(self, repository=None, tag=None):
        """
        Push image to registry. Raise exception when push fail.
        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: None
        """

        image = self

        if repository or tag:
            image = self.tag_image(repository, tag)

        for json_e in self.d.push(repository=image.name, tag=image.tag, stream=True, decode=True):
            logger.debug(json_e)
            status = graceful_get(json_e, "status")
            if status:
                logger.info(status)
            else:
                error = graceful_get(json_e, "error")
                if error is not None:
                    logger.error(status)
                    raise ConuException("There was an error while pushing the image %s: %s",
                                        self.name, error)
        return image

    def tag_image(self, repository=None, tag=None):
        """
        Apply additional tags to the image or even add a new name

        :param repository: str, see constructor
        :param tag: str, see constructor
        :return: instance of DockerImage
        """
        if not (repository or tag):
            raise ValueError("You need to specify either repository or tag.")
        r = repository or self.name
        t = "latest" if not tag else tag
        self.d.tag(image=self.get_full_name(), repository=r, tag=t)
        return DockerImage(r, tag=t)

    def inspect(self, refresh=True):
        """
        provide metadata about the image; flip refresh=True if cached metadata are enough

        :param refresh: bool, update the metadata with up to date content
        :return: dict
        """
        if refresh or not self._inspect_data:
            identifier = self._id or self.get_full_name()
            if not identifier:
                raise ConuException("This image does not have a valid identifier.")
            self._inspect_data = self.d.inspect_image(identifier)
        return self._inspect_data

    def rmi(self, force=False, via_name=False):
        """
        remove this image

        :param force: bool, force removal of the image
        :param via_name: bool, refer to the image via name, if false, refer via ID
        :return: None
        """
        self.d.remove_image(self.get_full_name() if via_name else self.get_id(), force=force)

    def mount(self, mount_point=None):
        """
        Provide access to filesystem of this docker image.

        :param mount_point: str, directory where the filesystem will be mounted; if not
                             provided, mkdtemp(dir="/var/tmp") is used
        :return: instance of :class:`conu.apidefs.filesystem.Filesystem`
        """
        return DockerImageViaArchiveFS(self, mount_point=mount_point)

    def _run_container(self, run_command_instance, callback):
        """ this is internal method """
        tmpfile = os.path.join(get_backend_tmpdir(), random_tmp_filename())
        # the cid file must not exist
        run_command_instance.options += ["--cidfile=%s" % tmpfile]
        logger.debug("docker command: %s" % run_command_instance)
        response = callback()

        def get_cont_id():
            if not os.path.exists(tmpfile):
                return False
            with open(tmpfile, 'r') as fd:
                content = fd.read()
            return bool(content)

        Probe(timeout=2, count=10, pause=0.1, fnc=get_cont_id).run()

        with open(tmpfile, 'r') as fd:
            container_id = fd.read()

        if not container_id:
            raise ConuException("We could not get container's ID, it probably was not created")
        return container_id, response

    def run_via_binary(self, run_command_instance=None, command=None, volumes=None,
                       additional_opts=None, **kwargs):
        """
        create a container using this image and run it in background;
        this method is useful to test real user scenarios when users invoke containers using
        binary

        :param run_command_instance: instance of DockerRunBuilder
        :param command: list of str, command to run in the container, examples:
            - ["ls", "/"]
            - ["bash", "-c", "ls / | grep bin"]
        :param volumes: tuple or list of tuples in the form:

            * `("/path/to/directory", )`
            * `("/host/path", "/container/path")`
            * `("/host/path", "/container/path", "mode")`
            * `(conu.Directory('/host/path'), "/container/path")` (source can be also
                Directory instance)

        :param additional_opts: list of str, additional options for `docker run`
        :return: instance of DockerContainer
        """

        logger.info("run container via binary in background")

        if (command is not None or additional_opts is not None) \
                and run_command_instance is not None:
            raise ConuException(
                "run_command_instance and command parameters cannot be passed "
                "into method at same time")

        if run_command_instance is None:
            command = command or []
            additional_opts = additional_opts or []

            if (isinstance(command, list) or isinstance(command, tuple) and
                isinstance(additional_opts, list) or isinstance(additional_opts, tuple)):
                run_command_instance = DockerRunBuilder(
                    command=command, additional_opts=additional_opts)
            else:
                raise ConuException("command and additional_opts needs to be list of str or None")
        else:
            run_command_instance = run_command_instance or DockerRunBuilder()
            if not isinstance(run_command_instance, DockerRunBuilder):
                raise ConuException(
                    "run_command_instance needs to be an instance of DockerRunBuilder")

        run_command_instance.image_name = self.get_id()
        run_command_instance.options += ["-d"]

        if volumes:
            run_command_instance.options += self.get_volume_options(volumes=volumes)

        def callback():
            try:
                # FIXME: catch std{out,err}, print stdout to logger.debug, stderr to logger.error
                run_cmd(run_command_instance.build())
            except subprocess.CalledProcessError as ex:
                raise ConuException("Container exited with an error: %s" % ex.returncode)

        container_id, _ = self._run_container(run_command_instance, callback)

        container_name = self.d.inspect_container(container_id)['Name'][1:]
        return DockerContainer(self, container_id, name=container_name)

    def run_via_binary_in_foreground(
            self, run_command_instance=None, command=None, volumes=None,
            additional_opts=None, popen_params=None, container_name=None):
        """
        Create a container using this image and run it in foreground;
        this method is useful to test real user scenarios when users invoke containers using
        binary and pass input into the container via STDIN. You are also responsible for:

         * redirecting STDIN when intending to use container.write_to_stdin afterwards by setting
              popen_params={"stdin": subprocess.PIPE} during run_via_binary_in_foreground

         * checking whether the container exited successfully via:
              container.popen_instance.returncode

        Please consult the documentation for subprocess python module for best practices on
        how you should work with instance of Popen

        :param run_command_instance: instance of DockerRunBuilder
        :param command: list of str, command to run in the container, examples:
            - ["ls", "/"]
            - ["bash", "-c", "ls / | grep bin"]
        :param volumes: tuple or list of tuples in the form:

            * `("/path/to/directory", )`
            * `("/host/path", "/container/path")`
            * `("/host/path", "/container/path", "mode")`
            * `(conu.Directory('/host/path'), "/container/path")` (source can be also
                Directory instance)

        :param additional_opts: list of str, additional options for `docker run`
        :param popen_params: dict, keyword arguments passed to Popen constructor
        :param container_name: str, pretty container identifier
        :return: instance of DockerContainer
        """
        logger.info("run container via binary in foreground")

        if (command is not None or additional_opts is not None) \
                and run_command_instance is not None:
            raise ConuException(
                "run_command_instance and command parameters cannot be "
                "passed into method at same time")

        if run_command_instance is None:
            command = command or []
            additional_opts = additional_opts or []

            if (isinstance(command, list) or isinstance(command, tuple) and
                isinstance(additional_opts, list) or isinstance(additional_opts, tuple)):
                run_command_instance = DockerRunBuilder(
                    command=command, additional_opts=additional_opts)
            else:
                raise ConuException("command and additional_opts needs to be list of str or None")
        else:
            run_command_instance = run_command_instance or DockerRunBuilder()
            if not isinstance(run_command_instance, DockerRunBuilder):
                raise ConuException("run_command_instance needs to be an "
                                    "instance of DockerRunBuilder")

        popen_params = popen_params or {}

        run_command_instance.image_name = self.get_id()
        if container_name:
            run_command_instance.options += ["--name", container_name]

        if volumes:
            run_command_instance.options += self.get_volume_options(volumes=volumes)

        def callback():
            return subprocess.Popen(run_command_instance.build(), **popen_params)

        container_id, popen_instance = self._run_container(run_command_instance, callback)

        actual_name = self.d.inspect_container(container_id)['Name'][1:]
        if container_name and container_name != actual_name:
            raise ConuException(
                "Unexpected container name value. Expected = "
                + str(container_name) + " Actual = " + str(actual_name))
        if not container_name:
            container_name = actual_name
        return DockerContainer(
            self, container_id, popen_instance=popen_instance, name=container_name)

    def run_via_api(self, container_params=None):
        """
        create a container using this image and run it in background via Docker-py API.
        https://docker-py.readthedocs.io/en/stable/api.html
        Note: If you are using Healthchecks, be aware that support of some options were introduced
        just with version of Docker-py API 1.29
        :param container_params: DockerContainerParameters
        :return: instance of DockerContainer
        """

        if not container_params:
            container_params = DockerContainerParameters()

        # Host-specific configuration
        host_config = self.d.create_host_config(auto_remove=container_params.remove,
                                                cap_add=container_params.cap_add,
                                                cap_drop=container_params.cap_drop,
                                                devices=container_params.devices,
                                                dns=container_params.dns,
                                                group_add=container_params.group_add,
                                                init=container_params.init,
                                                ipc_mode=container_params.ipc_mode,
                                                isolation=container_params.isolation,
                                                mem_limit=container_params.mem_limit,
                                                mounts=container_params.mounts,
                                                pids_limit=container_params.pids_limit,
                                                privileged=container_params.privileged,
                                                publish_all_ports=container_params.publish_all_ports,
                                                port_bindings=container_params.port_mappings,
                                                read_only=container_params.read_only)

        container = self.d.create_container(self.get_id(), command=container_params.command,
                                            detach=True,
                                            hostname=container_params.hostname,
                                            user=container_params.user,
                                            stdin_open=container_params.stdin_open,
                                            tty=container_params.tty,
                                            ports=container_params.exposed_ports,
                                            environment=container_params.env_variables,
                                            volumes=container_params.volumes,
                                            name=container_params.name,
                                            entrypoint=container_params.entrypoint,
                                            working_dir=container_params.working_dir,
                                            host_config=host_config,
                                            mac_address=container_params.mac_address,
                                            labels=container_params.labels,
                                            stop_signal=container_params.stop_signal,
                                            healthcheck=container_params.healthcheck,
                                            runtime=container_params.runtime)

        return DockerContainer(self, container['Id'], name=container_params.name)

    def run_in_pod(self, namespace="default"):
        """
        run image inside Kubernetes Pod
        :param namespace: str, name of namespace where pod will be created
        :return: Pod instance
        """

        core_api = get_core_api()

        image_data = self.get_metadata()

        pod = Pod.create(image_data)

        try:
            pod_instance = core_api.create_namespaced_pod(namespace=namespace, body=pod)
        except ApiException as e:
            raise ConuException("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)

        logger.info(
            "Starting Pod %s in namespace %s" % (pod_instance.metadata.name, namespace))

        return Pod(name=pod_instance.metadata.name,
                   namespace=pod_instance.metadata.namespace,
                   spec=pod_instance.spec)

    def has_pkgs_signed_with(self, allowed_keys):
        """
        Check signature of packages installed in image.
        Raises exception when

        * rpm binary is not installed in image
        * parsing of rpm fails
        * there are packages in image that are not signed with one of allowed keys

        :param allowed_keys: list of allowed keys
        :return: bool
        """

        if not allowed_keys or not isinstance(allowed_keys, list):
            raise ConuException("allowed_keys must be a list")
        command = ['rpm', '-qa', '--qf', '%{name} %{SIGPGP:pgpsig}\n']
        cont = self.run_via_binary(command=command)
        try:
            out = cont.logs_unicode()[:-1].split('\n')
            check_signatures(out, allowed_keys)
        finally:
            cont.stop()
            cont.delete()
        return True

    @staticmethod
    def get_volume_options(volumes):
        """
        Generates volume options to run methods.

        :param volumes: tuple or list of tuples in form target x source,target x source,target,mode.
        :return: list of the form ["-v", "/source:/target", "-v", "/other/source:/destination:z", ...]
        """
        if not isinstance(volumes, list):
            volumes = [volumes]
        volumes = [Volume.create_from_tuple(v) for v in volumes]
        result = []
        for v in volumes:
            result += ["-v", str(v)]
        return result

    @classmethod
    def build(cls, path, tag=None, dockerfile=None):
        """
        Build the image from the provided dockerfile in path

        :param path : str, path to the directory containing the Dockerfile
        :param tag: str, A tag to add to the final image
        :param dockerfile: str, path within the build context to the Dockerfile
        :return: instance of DockerImage
        """
        if not path:
            raise ConuException('Please specify path to the directory containing the Dockerfile')
        client = get_client()
        response = [line for line in client.build(path,
                                                  rm=True, tag=tag,
                                                  dockerfile=dockerfile,
                                                  quiet=True)]
        if not response:
            raise ConuException('Failed to get ID of image')

        # The expected output is just one line with image ID
        if len(response) > 1:
            raise ConuException('Build failed: ' + str(response))

        # get ID from output
        # b'{"stream":"sha256:39c7bac4e2da37983203df4fcf612a02de9e6f6456a7f3434d1fccbc9ad639a5\\n"}\r\n'
        response_utf = response[0].decode('utf-8')
        if response_utf[:11] != '{"stream":"' or response_utf[-6:] != '\\n"}\r\n':
            raise ConuException('Failed to parse ID from ' + response_utf)
        image_id = response_utf[11:-6]

        return cls(None, identifier=image_id)

    def get_layer_ids(self, rev=True):
        """
        Get IDs of image layers

        :param rev: get layers reversed
        :return: list of strings
        """
        layers = [x['Id'] for x in self.d.history(self.get_id())]
        if not rev:
            layers.reverse()
        return layers

    def layers(self, rev=True):
        """
        Get list of DockerImage for every layer in image

        :param rev: get layers rev
        :return: list of DockerImages
        """
        image_layers = [
            DockerImage(None, identifier=x, pull_policy=DockerImagePullPolicy.NEVER)
            for x in self.get_layer_ids()
        ]
        if not rev:
            image_layers.reverse()
        return image_layers

    def get_metadata(self):
        """
        Provide metadata about this image.

        :return: ImageMetadata, Image metadata instance
        """
        return inspect_to_metadata(self.metadata, self.inspect(refresh=True))


class S2IDockerImage(DockerImage, S2Image):
    def __init__(self, repository, tag="latest",  identifier=None,
                 pull_policy=DockerImagePullPolicy.IF_NOT_PRESENT):
        """
        :param repository: str, image name, examples: "fedora", "registry.fedoraproject.org/fedora",
                            "tomastomecek/sen", "docker.io/tomastomecek/sen"
        :param tag: str, tag of the image, when not specified, "latest" is implied
        :param identifier: str, unique identifier for this image
        :param pull_policy: enum, strategy to apply for pulling the image
        """
        super(S2IDockerImage, self).__init__(repository,
                                             tag=tag,
                                             identifier=identifier,
                                             pull_policy=pull_policy)
        self._s2i_exists = None

    def _s2i_command(self, args):
        """
        return s2i command to run

        :param args: list of str, arguments and options passed to s2i binary
        :return: list of str
        """
        s2i_command_exists()
        return ["s2i"] + args

    def extend(self, source, new_image_name, s2i_args=None):
        """
        extend this s2i-enabled image using provided source, raises ConuException if
        `s2i build` fails

        :param source: str, source used to extend the image, can be path or url
        :param new_image_name: str, name of the new, extended image
        :param s2i_args: list of str, additional options and arguments provided to `s2i build`
        :return: S2Image instance
        """
        s2i_args = s2i_args or []
        c = self._s2i_command(["build"] + s2i_args + [source, self.get_full_name()])
        if new_image_name:
            c.append(new_image_name)
        try:
            run_cmd(c)
        except subprocess.CalledProcessError as ex:
            raise ConuException("s2i build failed: %s" % ex)
        return S2IDockerImage(new_image_name)

    def usage(self):
        """
        Provide output of `s2i usage`

        :return: str
        """
        c = self._s2i_command(["usage", self.get_full_name()])
        with open(os.devnull, "w") as fd:
            process = subprocess.Popen(c, stdout=fd, stderr=subprocess.PIPE)
            _, output = process.communicate()
            retcode = process.poll()
        if retcode:
            raise ConuException("`s2i usage` failed: %s" % output)
        return output.decode("utf-8").strip()

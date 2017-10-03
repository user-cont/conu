# -*- coding: utf-8 -*-

import os
import subprocess
import time

from conu.backend.docker import DockerImage, DockerContainer, DockerRunCommand
from conu.utils.core import Volume, Probe, run_cmd
from avocado import Test


class PostgresqlContainerFactory(object):
    postgres_image = DockerImage("docker.io/postgres")
    database = "postgres"
    password = "mysecretpassword"
    user = "postgres"
    default_env = ["-it", "-e POSTGRES_PASSWORD=%s" % password]
    docker_add_params = []

    def __init__(self, docker_additional_params=None, docker_default_params=default_env, start=False):
        self.default_env = docker_default_params
        self.docker_add_params = docker_additional_params
        self.container = None
        if start:
            self.postgre_start()

    def postgre_start(self, docker_additional_params=None, docker_default_params=None):
        params = docker_default_params or self.default_env
        params += docker_additional_params or self.docker_add_params
        r = DockerRunCommand(additional_opts=params)
        self.container = DockerContainer.run_via_binary(self.postgres_image, r)
        Probe().wait_inet_port(self.container.get_IPv4s()[0], 5432, count=20)

    def life_check(self):
        my_env = os.environ.copy()
        my_env["PGPASSWORD"] = self.password
        try:
            run_cmd(["psql", "-h", self.container.get_IPv4s()[0], "-c", "SELECT 1",
                     self.database, self.user], env=my_env)
        except subprocess.CalledProcessError:
            return False
        return True

    def clean(self):
        self.container.rm(force=True)


class Basic(Test):
    def test_Pass(self):
        container = PostgresqlContainerFactory(start=True)
        self.assertTrue(container.life_check())
        container.clean()

    def test_additional_volume(self):
        container = PostgresqlContainerFactory()
        vol1 = Volume(target="/tmp", force_selinux=True)
        container.postgre_start(docker_additional_params=[vol1.docker()])
        self.assertTrue(container.life_check())
        container.container.execute("touch /tmp/xx")
        time.sleep(1)
        run_cmd("test -f %s/xx" % vol1.get_source())
        container.clean()
        vol1.clean()

    def test_NoOpFails(self):
        self.assertRaises(subprocess.CalledProcessError,
                          PostgresqlContainerFactory,
                          docker_default_params=["--abgc"],
                          start=True)

    def test_badInvocation(self):
        self.assertRaises(subprocess.CalledProcessError,
                          PostgresqlContainerFactory,
                          docker_additional_params=["-v aa:aa"],
                          start=True)


class MoreComplexExample(Test):
    def test_connection_between(self):
        volume = Volume(facl=['u:26:rwx'], target="/tmp")
        master = PostgresqlContainerFactory()
        master.postgre_start(docker_additional_params=[volume.docker()])

        self.assertTrue(master.life_check())

        slave = PostgresqlContainerFactory(start=True)
        self.assertTrue(slave.life_check())

        output = slave.container.execute("PGPASSWORD=%s psql -h %s -c 'SELECT 1' %s %s" %
                      (master.password, master.container.get_IPv4s()[0],
                       master.database, master.user))

        self.assertIn("1", output)
        master.clean()
        slave.clean()

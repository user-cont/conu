# -*- coding: utf-8 -*-

from conu.docker import *
from conu.utils import *
from avocado import Test
import os

class PostgresqlContainerFactory(Container):
    postgres_image = Image("docker.io/postgres")
    database = "postgres"
    password = "mysecretpassword"
    user = "postgres"
    default_env = ["-it", "-d", "-e POSTGRES_PASSWORD=%s" % (password)]
    docker_add_params = []

    def __init__(self, docker_additional_params=[], docker_default_params=default_env, start=False):
        super(PostgresqlContainerFactory,self).__init__(self.postgres_image)
        self.default_env = docker_default_params
        self.docker_add_params = docker_additional_params
        if start:
            self.postgre_start()

    def postgre_start(self, docker_additional_params=[], docker_default_params=[]):
        params_dir = docker_default_params or self.default_env
        params_dir += docker_additional_params or self.docker_add_params
        params = " ".join(params_dir)
        self.start(docker_params=params)
        Probe().wait_inet_port(self.get_ip(),5432, count=20)

    def life_check(self):
        my_env = os.environ.copy()
        my_env["PGPASSWORD"] = self.password
        try:
            run_cmd(["psql", "-h", self.get_ip(), "-c", "SELECT 1", self.database, self.user], env=my_env)
        except subprocess.CalledProcessError:
            return False
        return True


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
        container.execute("touch /tmp/xx")
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

        output = slave.execute("PGPASSWORD=%s psql -h %s -c 'SELECT 1' %s %s" %
                      (master.password, master.get_ip(), master.database, master.user))

        self.assertIn("1", output)
        master.clean()
        slave.clean()

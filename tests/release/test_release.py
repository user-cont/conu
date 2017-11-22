import os
import subprocess

import pytest
import pkg_resources


version = {}
# __file__/../../conu/version.py
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
with open(os.path.join(project_dir, "conu", "version.py")) as fp:
    exec(fp.read(), version)


@pytest.mark.release
def test_is_installable():
    """ test whether we can install from PyPI """
    cmd_base = ["-m", "pip", "install", "--user", "conu"]
    subprocess.check_call(["python2"] + cmd_base)
    subprocess.check_call(["python3"] + cmd_base)


@pytest.mark.release
def test_version_matches():
    """ test whether the latest version is up there """
    assert pkg_resources.get_distribution("conu").version == version["__version__"]
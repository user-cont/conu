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
import time

from conu import Probe, ProbeTimeout, CountExceeded

import pytest

ARGUMENT = "key"
MESSAGE = "It is both alive and dead"


def snoozer(seconds=1):
    time.sleep(seconds)
    return True


def value_err_raise():
    raise ValueError


class TestProbe(object):
    def test_in_backgroud(self):
        probe = Probe(timeout=5, pause=0.5, fnc=snoozer, seconds=2)

        probe.run()
        assert not probe.is_alive()

        probe.run_in_background()
        assert probe.is_alive()
        probe.terminate()
        probe.join()
        assert not probe.is_alive()

    def test_exception(self):

        # probe and caller in one thread
        # probe should ignore expected_exceptions
        start = time.time()
        probe = Probe(timeout=3, pause=0.5, expected_exceptions=ValueError, fnc=value_err_raise)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

        # probe should not ignore exceptions other than expected exceptions
        start = time.time()
        probe = Probe(timeout=5, pause=0.5, expected_exceptions=ImportError, fnc=value_err_raise)
        with pytest.raises(ValueError):
            probe.run()
        assert (time.time() - start) < 1, "Timeout exceeded"

        start = time.time()
        probe = Probe(timeout=5, pause=0.5, fnc=value_err_raise)
        with pytest.raises(ValueError):
            probe.run()
        assert (time.time() - start) < 1, "Timeout exceeded"

        # run in background
        # probe should ignore expected_exceptions
        start = time.time()
        probe = Probe(timeout=3, pause=0.5, expected_exceptions=ValueError, fnc=value_err_raise)
        probe.run_in_background()
        with pytest.raises(ProbeTimeout):
            probe.join()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

        # probe should not ignore exceptions other than expected exceptions
        start = time.time()
        probe = Probe(timeout=5, pause=0.5, expected_exceptions=ImportError, fnc=value_err_raise)
        probe.run_in_background()
        with pytest.raises(ValueError):
            probe.join()
        assert (time.time() - start) < 1, "Timeout exceeded"

        start = time.time()
        probe = Probe(timeout=5, pause=0.5, fnc=value_err_raise)
        probe.run_in_background()
        with pytest.raises(ValueError):
            probe.join()
        assert (time.time() - start) < 1, "Timeout exceeded"

    def test_count(self):
        def say_no():
            time.sleep(1)
            return False

        start = time.time()
        probe = Probe(timeout=5, count=1, pause=0.5, fnc=say_no)
        with pytest.raises(CountExceeded):
            probe.run()
        assert (time.time() - start) < 2, "Probe should end after one allowed try"

        start = time.time()
        probe = Probe(timeout=3, count=10, pause=0.5, fnc=say_no)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 3, "Probe should reach timeout"

        start = time.time()
        probe = Probe(timeout=5, count=0, pause=0.5, fnc=value_err_raise)
        with pytest.raises(CountExceeded):
            probe.run()
        assert (time.time() - start) < 2, "Probe should always end successfully with count=0 "

    def test_arguments(self):
        def check_arg(arg=""):
            return arg == ARGUMENT

        # probe should be able to pass arguments to function
        start = time.time()
        probe = Probe(timeout=5, pause=0.5, fnc=check_arg, arg=ARGUMENT)
        probe.run()
        assert (time.time() - start) < 1, "Timeout exceeded"

        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=check_arg, arg="devil")
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

    def test_reach_timeout(self):
        # probe should reach timeout with long-running function calls
        # probe and caller in one thread
        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=snoozer, seconds=10)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

        # in background
        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=snoozer, seconds=10)
        probe.run_in_background()
        with pytest.raises(ProbeTimeout):
            probe.join()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

    def test_expected_retval(self):
        def truth():
            return MESSAGE

        def lie():
            return "Box is empty"

        # probe should end when expected_retval is reached
        start = time.time()
        probe = Probe(timeout=5, pause=0.5, fnc=truth, expected_retval=MESSAGE)
        probe.run()
        assert (time.time() - start) < 1, "Timeout exceeded"

        # probe should reach timeout when expected_retval is not reached
        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=lie, expected_retval=MESSAGE)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

    def test_concurrency(self):
        pool = []
        for i in range(3):
            probe = Probe(timeout=10, fnc=snoozer, seconds=3)
            probe.run_in_background()
            pool.append(probe)

        for p in pool:
            assert p.is_alive()

        for p in pool:
            p.terminate()
            p.join()

        for p in pool:
            assert not p.is_alive()

from conu.utils.probes import Probe, ProbeTimeout
import time

import pytest

ARGUMENT = "key"
MESSAGE = "It is both alive and dead"


def sleeper(seconds=1):
    time.sleep(seconds)
    return True


class TestProbe(object):
    def test_exception(self):
        def value_err_raise():
            raise ValueError

        start = time.time()
        probe = Probe(timeout=3, pause=0.5, expected_exceptions=ValueError, fnc=value_err_raise)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

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

    def test_arguments(self):
        def check_arg(arg=""):
            return arg == ARGUMENT

        start = time.time()
        probe = Probe(timeout=5, pause=0.5, fnc=check_arg, arg=ARGUMENT)
        probe.run()
        assert (time.time() - start) < 1, "Timeout exceeded"

        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=check_arg, arg="devil")
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

    def test_kill_process(self):
        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=sleeper, seconds=10)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

    def test_expected_retval(self):
        def truth():
            return MESSAGE

        def lie():
            return "Box is empty"

        start = time.time()
        probe = Probe(timeout=5, pause=0.5, fnc=truth, expected_retval=MESSAGE)
        probe.run()
        assert (time.time() - start) < 1, "Timeout exceeded"

        start = time.time()
        probe = Probe(timeout=3, pause=0.5, fnc=lie, expected_retval=MESSAGE)
        with pytest.raises(ProbeTimeout):
            probe.run()
        assert (time.time() - start) > 2, "Timeout not reached with unsuccessful function"

    def test_in_backgroud(self):
        probe = Probe(timeout=5, pause=0.5, fnc=sleeper, seconds=2)

        probe.run()
        assert not probe.is_alive()

        probe.run_in_background()
        assert probe.is_alive()
        probe.terminate()
        probe.join()
        assert not probe.is_alive()

    def test_concurrency(self):
        pool = []
        for i in range(3):
            probe = Probe(timeout=10, fnc=sleeper, seconds=3)
            probe.run_in_background()
            pool.append(probe)

        for p in pool:
            assert p.is_alive()

        for p in pool:
            p.terminate()
            p.join()

        for p in pool:
            assert not p.is_alive()

import time
import logging
from multiprocessing import Process, Queue

logger = logging.getLogger(__name__)


class Probe(object):
    """
    Probe can be used for waiting on specific result of a function.
    Probe ends when function returns expected_retval or timeout is exceeded.

    Attributes:
        timeout              Amount of time spent on trying
        pause                Amount of time waited between multiple function result checks
        expected_exceptions  When one of expected_exception is raised, probe ignores it and tries to run function again
        expected_retval      When expected_retval is recieved, probe ends successfully
        fnc                  Function which run is checked by probe
    """
    def __init__(self,
                 timeout=1,
                 pause=1,
                 expected_exceptions=(),
                 expected_retval=True,
                 fnc=bool,
                 **kwargs):
        self.probe = _ProbeHelper(timeout=timeout, pause=pause,
                                  expected_exceptions=expected_exceptions,
                                  expected_retval=expected_retval, fnc=fnc, **kwargs)
        self.process = None

    def run(self):
        return self.probe.run()

    def run_in_backgroud(self):
        self.process = Process(target=self.probe.run)
        return self.process.start()

    def terminate(self):
        if not self.process:
            return
        self.process.terminate()

    def join(self):
        if not self.process:
            return
        self.process.join()

    def is_alive(self):
        if not self.process:
            return False
        return self.process.is_alive()


class _ProbeHelper(object):
    def __init__(self,
                 timeout=1,
                 pause=1,
                 expected_exceptions=(),
                 expected_retval=True,
                 fnc=bool,
                 **kwargs):
        self.timeout = timeout
        self.pause = pause
        self.expected_exceptions = expected_exceptions
        self.fnc = fnc
        self.kwargs = kwargs
        self.expected_retval = expected_retval

    def _wrapper(self, q, start):
        """
        _wrapper checks return status of Probe.fnc and provides the result for process managing

        :param q:     Queue for function results
        :param start: Time of function run (used for logging)
        :return:      Return value or Exception
        """
        logger.debug("Running \"%s\" with parameters: \"%s\":\t%s/%s"
                     % (self.fnc.__name__, str(self.kwargs), round(time.time() - start), self.timeout))
        try:
            q.put(self.fnc(**self.kwargs))
        except self.expected_exceptions:
            q.put(False)
        except Exception as e:
            q.put(e)

    def run(self):
        start = time.time()
        queue = Queue()
        p = Process(target=self._wrapper, args=(queue, start))
        p.start()
        while time.time() - start <= self.timeout:
            if p.is_alive():
                time.sleep(self.pause)
            elif not queue.empty():
                result = queue.get()
                if isinstance(result, Exception):
                    raise result
                elif not (result == self.expected_retval):
                    p.join()
                    p = Process(target=self._wrapper, args=(queue, start))
                    p.start()
                else:
                    return True
            else:
                return True
        else:
            p.terminate()
            p.join()
            raise ProbeTimeout("Timeout exceeded.")


class ProbeTimeout(Exception):
    pass

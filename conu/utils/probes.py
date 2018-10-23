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
import logging

from multiprocessing import Process, Queue

from conu.exceptions import ConuException

logger = logging.getLogger(__name__)


class Probe(object):
    """
    Probe can be used for waiting on specific result of a function.
    Probe ends when function returns expected_retval or timeout is exceeded.

    """
    def __init__(self,
                 timeout=1,
                 pause=1,
                 count=-1,
                 expected_exceptions=(),
                 expected_retval=True,
                 fnc=bool,
                 **kwargs):
        """
        :param timeout:              Number of seconds spent on trying. Set timeout to -1 for infinite run.
        :param pause:                Number of seconds waited between multiple function result checks
        :param count:                Maximum number of tries, defaults to infinite, represented by -1
        :param expected_exceptions:  When one of expected_exception is raised, probe ignores it and
                                     tries to run function again. To ignore multiple exceptions use
                                     parenthesized tuple.
        :param expected_retval:      When expected_retval is received, probe ends successfully
        :param fnc:                  Function which run is checked by probe
        """
        self.timeout = timeout
        self.pause = pause
        self.count = count
        self.expected_exceptions = expected_exceptions
        self.fnc = fnc
        self.kwargs = kwargs
        self.expected_retval = expected_retval
        self.process = None
        self.queue = None

    def run(self):
        if self.process and self.process.is_alive():
            raise RuntimeError("One instance of Probe can only be probing once at any given time")
        return self._run()

    def run_in_background(self):
        if self.process and self.process.is_alive():
            raise RuntimeError("One instance of Probe can only be probing once at any given time")
        self.queue = Queue()
        self.process = Process(target=self._run)
        return self.process.start()

    def terminate(self):
        if not self.process:
            return
        self.process.terminate()

    def join(self):
        if not self.process:
            return
        self.process.join()
        if self.queue and not self.queue.empty():
            result = self.queue.get()
            if isinstance(result, Exception):
                raise result

    def is_alive(self):
        if not self.process:
            return False
        return self.process.is_alive()

    def _wrapper(self, q, start):
        """
        _wrapper checks return status of Probe.fnc and provides the result for process managing

        :param q:     Queue for function results
        :param start: Time of function run (used for logging)
        :return:      Return value or Exception
        """
        try:
            func_name = self.fnc.__name__
        except AttributeError:
            func_name = str(self.fnc)
        logger.debug("Running \"%s\" with parameters: \"%s\":\t%s/%s"
                     % (func_name, str(self.kwargs), round(time.time() - start), self.timeout))
        try:
            result = self.fnc(**self.kwargs)
            # let's log only first 50 characters of the response
            logger.debug("callback result = %s", str(result)[:50])
            q.put(result)
        except self.expected_exceptions as ex:
            logger.debug("expected exception was caught: %s", ex)
            q.put(False)
        except Exception as ex:
            logger.debug("adding exception %s to queue", ex)
            q.put(ex)

    def _run(self):
        start = time.time()
        fnc_queue = Queue()
        logger.debug("starting probe")
        p = Process(target=self._wrapper, args=(fnc_queue, start))
        p.start()
        logger.debug("first process started: pid=%s", p.pid)
        tries = 1
        while tries <= self.count or self.count == -1:
            elapsed = time.time() - start
            if self.timeout != -1 and elapsed > self.timeout:
                logger.info("timeout was reached, elapsed: %s", elapsed)
                break
            if p.is_alive():
                logger.debug("pausing for %s before next try", self.pause)
                time.sleep(self.pause)
            else:
                logger.debug("waiting for process to end...")
                p.join()
                if fnc_queue.empty():
                    raise RuntimeError("queue is empty when it shouldn't be")
                result = fnc_queue.get()
                logger.debug("result = %s", result)
                if isinstance(result, Exception):
                    # TODO: use result's traceback
                    if self.queue:
                        self.queue.put(result)
                        return False
                    else:
                        raise result
                elif not (result == self.expected_retval):
                    logger.debug("process ended, about to start another one")
                    p = Process(target=self._wrapper, args=(fnc_queue, start))
                    p.start()
                    tries += 1
                    logger.debug("attempt no. %s started, pid: %s", tries, p.pid)
                else:
                    return True
        p.terminate()
        p.join()
        if -1 < self.count < tries:
            e = CountExceeded()
        else:
            e = ProbeTimeout("Timeout exceeded.")
        logger.warning("probe is unsuccessful: %s", e)
        if self.queue:
            self.queue.put(e)
        else:
            raise e


class ProbeTimeout(ConuException):
    pass


class CountExceeded(ConuException):
    pass

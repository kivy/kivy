from asyncio.events import AbstractEventLoop
from asyncio.base_events import BaseEventLoop
from asyncio import events, SelectorEventLoop
import asyncio
import concurrent
import threading
from asyncio import futures

_MAX_WORKERS = 10


class GuiEventLoop(SelectorEventLoop):
    # Methods returning Futures for interacting with threads.

    def stop(self):
        # self._io_event_loop.stop()
        pass

    def wrap_future(self, future):
        """XXX"""
        if isinstance(future, futures.Future):
            return future  # Don't wrap our own type of Future.
        new_future = futures.Future()
        future.add_done_callback(
            lambda future:
                self.call_soon_threadsafe(
                    futures._copy_future_state, future, new_future))
        return new_future

    def run_until_complete(self, future, timeout=None):  # NEW!
        """Run the event loop until a Future is done.

        Return the Future's result, or raise its exception.

        If timeout is not None, run it for at most that long;
        if the Future is still not done, raise TimeoutError
        (but don't cancel the Future).
        """
        print("run_until_complete called")
        assert isinstance(future, futures.Future)

        # signal = threading.Condition()
        if timeout is None:
            while not future.done():
                self.run_once()
        else:
            raise Exception('Not implemented: timeouts until complete')

        return future.result()

    def call_repeatedly(self, interval, callback, *args):  # NEW!
        return _CancelJobRepeatedly(self, interval, callback, args)

    def call_soon(self, callback, *args):
        return self.call_later(0, callback, *args)

    def call_soon_threadsafe(self, callback, *args):
        return self.call_soon(callback, *args)

    def run_in_executor(self, executor, callback, *args):
        if isinstance(callback, asyncio.Handle):
            assert not args
            assert not isinstance(callback, asyncio.TimerHandle)
            if callback.cancelled:
                f = futures.Future()
                f.set_result(None)
                return f
            callback, args = callback.callback, callback.args
        if executor is None:
            executor = self._default_executor
            if executor is None:
                executor = concurrent.futures.ThreadPoolExecutor(_MAX_WORKERS)
                self._default_executor = executor
        return self.wrap_future(executor.submit(callback, *args))


class _CancelJobRepeatedly(object):
    """Object that allows cancelling of a call_repeatedly"""
    def __init__(self, event_loop, delay, callback, args):
        self.event_loop = event_loop
        self.delay = delay
        self.callback = callback
        self.args = args
        self.post()

    def invoke(self):
        self.callback(*self.args)
        self.post()

    def post(self):
        self.canceler = self.event_loop.call_later(self.delay, self.invoke)

    def cancel(self):
        self.canceler.cancel()

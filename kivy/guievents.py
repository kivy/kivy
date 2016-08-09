from asyncio.events import AbstractEventLoop
from asyncio.base_events import BaseEventLoop
from asyncio import events
import asyncio
import concurrent
import threading
from asyncio import futures

_MAX_WORKERS = 10


class GuiEventLoop(BaseEventLoop):
    # Methods returning Futures for interacting with threads.
    def __init__(self):
        super().__init__()
        self._start_io_event_loop()

    def _start_io_event_loop(self):
        """Starts the I/O event loop which we defer to for doing I/O
        running on another thread
        """
        self._event_loop_started = threading.Lock()
        self._event_loop_started.acquire()
        threading.Thread(None, self._io_event_loop_thread, daemon=True).start()
        self._event_loop_started.acquire()

    def _io_event_loop_thread(self):
        """Worker thread for running the I/O event loop"""
        io_event_loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(io_event_loop)
        assert isinstance(io_event_loop, AbstractEventLoop)
        self._io_event_loop = io_event_loop
        self._event_loop_started.release()
        self._io_event_loop.run_forever()

    def stop(self):
        self._io_event_loop.stop()

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
        assert isinstance(future, futures.Future)

        signal = threading.Condition()
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

    def _io_helper(self, target, args, kwargs):
        lock = threading.Lock()
        lock.acquire()
        res = None

        def helper_target():
            # nonlocal res
            res = target(*args, **kwargs)
            lock.release()

        handler = self._io_event_loop.call_soon_threadsafe(helper_target)
        lock.acquire()
        return res

    # Network I/O methods returning Futures.
    def getaddrinfo(
        self, host, port, *, family=0, type=0, proto=0, flags=0
    ):
        return self._io_helper(
            self._io_event_loop.getaddrinfo,
            (host, port),
            {
                'family': family,
                'type': type,
                'proto': proto,
                'flags': flags
            }
        )

    def getnameinfo(self, sockaddr, flags=0):
        return self._io_helper(
            self._io_event_loop.getnameinfo,
            (sockaddr, flags),
            {}
        )

    def create_connection(self, protocol_factory, host=None, port=None, *,
                          family=0, proto=0, flags=0, sock=None):
        return self._io_helper(
            self._io_event_loop.create_connection,
            (protocol_factory, host, port),
            {
                'family': family,
                'proto': proto,
                'flags': flags,
                'sock': sock
            }
        )

    def start_serving(self, protocol_factory, host=None, port=None, *,
                      family=0, proto=0, flags=0, sock=None):
        return self._io_helper(
            self._io_event_loop.start_serving,
            (protocol_factory, host, port),
            {
                'family': family,
                'proto': proto,
                'flags': flags,
                'sock': sock
            }
        )

    # Ready-based callback registration methods.
    # The add_*() methods return a Handler.
    # The remove_*() methods return True if something was removed,
    # False if there was nothing to delete.

    def _handler_helper(self, target, *args):
        lock = threading.Lock()
        lock.acquire()
        handler = None

        def helper_target():
            nonlocal handler
            handler = target(*args)
            lock.release()

        self._io_event_loop.call_soon_threadsafe(helper_target)
        lock.acquire()
        return handler

    def add_reader(self, fd, callback, *args):
        return _ready_helper(
            self._io_event_loop.add_reader, fd, callback, *args)

    def remove_reader(self, fd):
        return _ready_helper(self._io_event_loop.remove_reader, fd)

    def add_writer(self, fd, callback, *args):
        return _ready_helper(
            self._io_event_loop.add_writer, fd, callback, *args)

    def remove_writer(self, fd):
        return _ready_helper(self._io_event_loop.remove_writer, fd)

    # Completion based I/O methods returning Futures.

    def sock_recv(self, sock, nbytes):
        return self._io_helper(
            self._io_event_loop.sock_recv,
            (sock, nbytes),
            {}
        )

    def sock_sendall(self, sock, data):
        return self._io_helper(
            self._io_event_loop.sock_sendall,
            (sock, data),
            {}
        )

    def sock_connect(self, sock, address):
        return self._io_helper(
            self._io_event_loop.sock_connect,
            (sock, address),
            {}
        )
        # return self.run_in_executor(None, sock.connect, address)

    def sock_accept(self, sock):
        return self._io_helper(
            self._io_event_loop.sock_accept,
            (sock, ),
            {}
        )

    # Signal handling.

    def add_signal_handler(self, sig, callback, *args):
        return self._handler_helper(
            self.add_signal_handler, sig, callback, *args)

    def remove_signal_handler(self, sig):
        return self._handler_helper(self.remove_signal_handler, sig)


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

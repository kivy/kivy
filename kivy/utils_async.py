'''Async version of :mod:`kivy.utils`.
===========================================
'''

import os
from collections import deque

if os.environ.get('KIVY_EVENTLOOP', 'default') == 'trio':
    import trio
    async_lib = trio
else:
    import asyncio
    async_lib = asyncio
    trio = None


class AsyncCallbackQueue(object):
    '''A class for asynchronously iterating values in a queue and waiting
    for the queue to be updated with new values through a callback function.

    An instance is an async iterator which for every iteration waits for
    callbacks to add values to the queue and then returns it.

    :Parameters:

        `filter`: callable or None
            A callable that is called with :meth:`callback`'s positional
            arguments. When provided, if it returns false, this call is dropped.
        `convert`: callable or None
            A callable that is called with :meth:`callback`'s positional
            arguments. It is called immediately as opposed to async.
            If provided, the return value of convert is returned by
            the iterator rather than the original value. Helpful
            for callback values that need to be processed immediately.
        `maxlen`: int or None
            If None, the callback queue may grow to an arbitrary length.
            Otherwise, it is bounded to maxlen. Once it's full, when new items
            are added a corresponding number of oldest items are discarded.
        `thread_fn`: callable or None
            If reading from the queue is done with a different thread than
            writing it, this is the callback that schedules in the read thread.

    .. versionadded:: 1.10.1
    '''

    quit = False

    def __init__(self, filter=None, convert=None, maxlen=None, thread_fn=None,
                 **kwargs):
        super(AsyncCallbackQueue, self).__init__(**kwargs)
        self.filter = filter
        self.convert = convert
        self.callback_result = deque(maxlen=maxlen)
        self.thread_fn = thread_fn
        self.event = async_lib.Event()

    def __del__(self):
        self.stop()

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.event.clear()
        while not self.callback_result and not self.quit:
            await self.event.wait()
            self.event.clear()

        if self.callback_result:
            return self.callback_result.popleft()
        raise StopAsyncIteration

    def _thread_reentry(self, *largs, **kwargs):
        self.event.set()

    def callback(self, *args):
        '''This (and only this) function may be executed from another thread
        because the callback may be bound to code executing from an external
        thread.
        '''
        f = self.filter
        if self.quit or f and not f(*args):
            return

        convert = self.convert
        if convert:
            args = convert(*args)

        self.callback_result.append(args)

        thread_fn = self.thread_fn
        if thread_fn is None:
            self.event.set()
        else:
            thread_fn(self._thread_reentry)

    def stop(self):
        '''Stops the iterator and cleans up.
        '''
        self.quit = True
        self.event.set()


def _report_kivy_back_in_trio_thread_fn(task_container):
    # This function gets scheduled into the trio run loop to deliver the
    # thread's result.
    def do_release_then_return_result():
        # if canceled, do the cancellation otherwise the result.
        if task_container[1] is not None:
            task_container[1]()
        return task_container[2].unwrap()

    result = trio.hazmat.Result.capture(do_release_then_return_result)
    trio.hazmat.reschedule(task_container[0], result)


async def trio_run_in_kivy_thread(sync_fn, *args, cancellable=False):
    '''When canceled, executed work is discarded.
    '''
    if trio is None:
        raise Exception('trio is required but was not found')
    task_container = [None, ] * 4

    def kivy_thread_callback(*largs):
        # This is the function that runs in the worker thread to do the actual
        # work and then schedule the calls to report_back_in_trio_thread_fn
        if task_container[1] is None:
            task_container[2] = trio.hazmat.Result.capture(sync_fn, *args)

        try:
            task_container[3].run_sync_soon(
                _report_kivy_back_in_trio_thread_fn, task_container)
        except trio.RunFinishedError:
            # The entire run finished, so our particular tasks are certainly
            # long gone - it must have cancelled. Continue eating the queue.
            raise  # pass

    @trio.hazmat.enable_ki_protection
    async def schedule_kivy_thread():
        await trio.hazmat.checkpoint_if_cancelled()
        # Holds a reference to the task that's blocked in this function waiting
        # for the result as well as to the cancel callback and the result
        # (when not canceled).
        task_container[0] = trio.hazmat.current_task()
        task_container[3] = trio.hazmat.current_trio_token()
        from kivy.clock import Clock
        Clock.schedule_once(kivy_thread_callback, 0)

        def abort(raise_cancel):
            if cancellable:
                task_container[1] = raise_cancel
            return trio.hazmat.Abort.FAILED
        return await trio.hazmat.wait_task_rescheduled(abort)

    return await schedule_kivy_thread()

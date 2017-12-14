'''Async version of :mod:`kivy.utils`.
===========================================
'''

from kivy.compat import async_coroutine, aiter_compat
import asyncio
import os
from collections import deque

if os.environ.get('KIVY_EVENTLOOP', 'default') == 'trio':
    import trio
    async_lib = trio
else:
    async_lib = asyncio


class AsyncCallbackQueue(object):
    '''A class for asynchronously iterating values in a queue and waiting
    for the queue to be updated with new values through a callback function.

    An instance is an async iterator which for every iteration waits for
    callbacks to add values to the queue and then returns it.

    :Parameters:

        `loop`: event loop instance
            The asyncio event loop to use. If None, the default,
            asyncio.get_event_loop() is used.
        `filter`: callable or None
            A function that is called with the value that the callback adds.
            When provided, if the function returns False the value is
            ignored and not returned by the iterator, otherwise it is returned.
        `convert`: callable or None
            A function that is called with the value that the callback adds.
            If provided, the return value of convert is returned by
            the iterator rather than the original value. Helpful
            for callback values that need to be processed immediately.

    .. versionadded:: 1.10.1
    '''

    callback_result = []

    event = None

    loop = None

    quit = False

    filter = None

    convert = None

    def __init__(self, loop=None, filter=None, convert=None, maxlen=None,
                 **kwargs):
        super(AsyncCallbackQueue, self).__init__(**kwargs)
        self.filter = filter
        self.convert = convert
        self.callback_result = deque(maxlen=maxlen)
        self.loop = loop or asyncio.get_event_loop()
        self.event = async_lib.Event()

    def __del__(self):
        self.stop()

    @aiter_compat
    def __aiter__(self):
        return self

    @async_coroutine
    def __anext__(self):
        self.event.clear()
        while not self.callback_result and not self.quit:
            yield from self.event.wait()
            self.event.clear()

        if self.callback_result:
            return self.callback_result.popleft()
        raise StopAsyncIteration

    def callback(self, *args):
        f = self.filter
        if f and not f(args):
            return

        convert = self.convert
        if convert:
            args = convert(args)

        self.callback_result.append(args)
        self.event.set()

    def stop(self):
        '''Stops the iterator and cleans up.
        '''
        self.quit = True
        self.event.set()

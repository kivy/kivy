'''Async version of :mod:`kivy.app`.
===========================================
'''

from kivy.base import async_runTouchApp


class AsyncApp(object):

    async def async_run(self):
        '''Identical to :meth:`run`, but is a coroutine and can be
        scheduled in a running async event loop.

        .. versionadded:: 1.10.1
        '''
        self._run_prepare()
        await async_runTouchApp()
        self.stop()

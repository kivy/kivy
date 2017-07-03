'''Async version of :mod:`kivy.base`.
===========================================
'''

from kivy.compat import async_coroutine
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
import asyncio


class AsyncEventLoopBase(object):

    @async_coroutine
    def async_mainloop(self):
        from kivy.base import ExceptionManager, stopTouchApp
        while not self.quit and self.status == 'started':
            try:
                yield from self.async_idle()
                if self.window:
                    self.window.mainloop()
            except BaseException as inst:
                # use exception manager first
                r = ExceptionManager.handle_exception(inst)
                if r == ExceptionManager.RAISE:
                    stopTouchApp()
                    raise
                else:
                    pass

    @async_coroutine
    def async_idle(self):
        '''Identical to :meth:`idle`, but instead used when running
        within an async event loop.
        '''

        # update dt
        yield from Clock.async_tick()

        # read and dispatch input from providers
        self.dispatch_input()

        # flush all the canvas operation
        Builder.sync()

        # tick before draw
        Clock.tick_draw()

        # flush all the canvas operation
        Builder.sync()

        window = self.window
        if window and window.canvas.needs_redraw:
            window.dispatch('on_draw')
            window.dispatch('on_flip')

        # don't loop if we don't have listeners !
        if len(self.event_listeners) == 0:
            Logger.error('Base: No event listeners have been created')
            Logger.error('Base: Application will leave')
            self.exit()
            return False

        return self.quit

    def async_run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_mainloop())
        loop.close()


@async_coroutine
def async_runTouchApp(widget=None, slave=False):
    '''Identical to :func:`runTouchApp` but instead is a coroutine
    that can be run in an existing async event loop.

    .. versionadded:: 1.10.1
    '''
    from kivy.base import _runTouchApp_prepare, stopTouchApp, EventLoop
    _runTouchApp_prepare(widget=widget, slave=slave)

    # we are in a slave mode, don't do dispatching.
    if slave:
        return

    try:
        yield from EventLoop.async_mainloop()
    finally:
        stopTouchApp()

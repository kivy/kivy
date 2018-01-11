'''Async version of :mod:`kivy.base`.
===========================================
'''

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder


class AsyncEventLoopBase(object):

    async def async_mainloop(self):
        from kivy.base import ExceptionManager, stopTouchApp
        while not self.quit and self.status == 'started':
            try:
                await self.async_idle()
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

    async def async_idle(self):
        '''Identical to :meth:`idle`, but instead used when running
        within an async event loop.
        '''

        # update dt
        await Clock.async_tick()

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


async def async_runTouchApp(widget=None, slave=False):
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
        await EventLoop.async_mainloop()
    finally:
        stopTouchApp()

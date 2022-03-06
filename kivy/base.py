# pylint: disable=W0611
'''
Kivy Base
=========

This module contains the Kivy core functionality and is not intended for end
users. Feel free to look through it, but bare in mind that calling any of
these methods directly may result in an unpredictable behavior as the calls
access directly the event loop of an application.
'''

__all__ = (
    'EventLoop',
    'EventLoopBase',
    'ExceptionHandler',
    'ExceptionManagerBase',
    'ExceptionManager',
    'runTouchApp',
    'async_runTouchApp',
    'stopTouchApp',
)

import sys
import os
from kivy.config import Config
from kivy.logger import Logger
from kivy.utils import platform
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.context import register_context

# private vars
EventLoop = None


class ExceptionHandler(object):
    '''Base handler that catches exceptions in :func:`runTouchApp`.
    You can subclass and extend it as follows::

        class E(ExceptionHandler):
            def handle_exception(self, inst):
                Logger.exception('Exception caught by ExceptionHandler')
                return ExceptionManager.PASS

        ExceptionManager.add_handler(E())

    Then, all exceptions will be set to PASS, and logged to the console!
    '''

    def handle_exception(self, exception):
        '''Called by :class:`ExceptionManagerBase` to handle a exception.

        Defaults to returning :attr:`ExceptionManager.RAISE` that re-raises the
        exception. Return :attr:`ExceptionManager.PASS` to indicate that the
        exception was handled and should be ignored.

        This may be called multiple times with the same exception, if
        :attr:`ExceptionManager.RAISE` is returned as the exception bubbles
        through multiple kivy exception handling levels.
        '''
        return ExceptionManager.RAISE


class ExceptionManagerBase:
    '''ExceptionManager manages exceptions handlers.'''

    RAISE = 0
    """The exception should be re-raised.
    """
    PASS = 1
    """The exception should be ignored as it was handled by the handler.
    """

    def __init__(self):
        self.handlers = []
        self.policy = ExceptionManagerBase.RAISE

    def add_handler(self, cls):
        '''Add a new exception handler to the stack.'''
        if cls not in self.handlers:
            self.handlers.append(cls)

    def remove_handler(self, cls):
        '''Remove the exception handler from the stack.'''
        if cls in self.handlers:
            self.handlers.remove(cls)

    def handle_exception(self, inst):
        '''Called when an exception occurred in the :func:`runTouchApp`
        main loop.'''
        ret = self.policy
        for handler in self.handlers:
            r = handler.handle_exception(inst)
            if r == ExceptionManagerBase.PASS:
                ret = r
        return ret


#: Instance of a :class:`ExceptionManagerBase` implementation.
ExceptionManager: ExceptionManagerBase = register_context(
    'ExceptionManager', ExceptionManagerBase)
"""The :class:`ExceptionManagerBase` instance that handles kivy exceptions.
"""


class EventLoopBase(EventDispatcher):
    '''Main event loop. This loop handles the updating of input and
    dispatching events.
    '''

    __events__ = ('on_start', 'on_pause', 'on_stop')

    def __init__(self):
        super(EventLoopBase, self).__init__()
        self.quit = False
        self.input_events = []
        self.postproc_modules = []
        self.status = 'idle'
        self.stopping = False
        self.input_providers = []
        self.input_providers_autoremove = []
        self.event_listeners = []
        self.window = None
        self.me_list = []

    @property
    def touches(self):
        '''Return the list of all touches currently in down or move states.
        '''
        return self.me_list

    def ensure_window(self):
        '''Ensure that we have a window.
        '''
        import kivy.core.window  # NOQA
        if not self.window:
            Logger.critical('App: Unable to get a Window, abort.')
            sys.exit(1)

    def set_window(self, window):
        '''Set the window used for the event loop.
        '''
        self.window = window

    def add_input_provider(self, provider, auto_remove=False):
        '''Add a new input provider to listen for touch events.
        '''
        if provider not in self.input_providers:
            self.input_providers.append(provider)
            if auto_remove:
                self.input_providers_autoremove.append(provider)

    def remove_input_provider(self, provider):
        '''Remove an input provider.

        .. versionchanged:: 2.1.0
            Provider will be also removed if it exist in auto-remove list.
        '''
        if provider in self.input_providers:
            self.input_providers.remove(provider)
            if provider in self.input_providers_autoremove:
                self.input_providers_autoremove.remove(provider)

    def add_event_listener(self, listener):
        '''Add a new event listener for getting touch events.
        '''
        if listener not in self.event_listeners:
            self.event_listeners.append(listener)

    def remove_event_listener(self, listener):
        '''Remove an event listener from the list.
        '''
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)

    def start(self):
        '''Must be called before :meth:`EventLoopBase.run()`. This starts all
        configured input providers.

        .. versionchanged:: 2.1.0
            Method can be called multiple times, but event loop will start only
            once.
        '''
        if self.status == 'started':
            return
        self.status = 'started'
        self.quit = False
        Clock.start_clock()
        for provider in self.input_providers:
            provider.start()
        self.dispatch('on_start')

    def close(self):
        '''Exit from the main loop and stop all configured
        input providers.'''
        self.quit = True
        self.stop()
        self.status = 'closed'

    def stop(self):
        '''Stop all input providers and call callbacks registered using
        `EventLoop.add_stop_callback()`.

        .. versionchanged:: 2.1.0
            Method can be called multiple times, but event loop will stop only
            once.
        '''
        if self.status != 'started':
            return
        # XXX stop in reverse order that we started them!! (like push
        # pop), very important because e.g. wm_touch and WM_PEN both
        # store old window proc and the restore, if order is messed big
        # problem happens, crashing badly without error
        for provider in reversed(self.input_providers[:]):
            provider.stop()
            self.remove_input_provider(provider)

        # ensure any restart will not break anything later.
        self.input_events = []

        Clock.stop_clock()
        self.stopping = False
        self.status = 'stopped'
        self.dispatch('on_stop')

    def add_postproc_module(self, mod):
        '''Add a postproc input module (DoubleTap, TripleTap, DeJitter
        RetainTouch are defaults).'''
        if mod not in self.postproc_modules:
            self.postproc_modules.append(mod)

    def remove_postproc_module(self, mod):
        '''Remove a postproc module.'''
        if mod in self.postproc_modules:
            self.postproc_modules.remove(mod)

    def remove_android_splash(self, *args):
        '''Remove android presplash in SDL2 bootstrap.'''
        try:
            from android import remove_presplash
            remove_presplash()
        except ImportError:
            Logger.warning(
                'Base: Failed to import "android" module. '
                'Could not remove android presplash.')
            return

    def post_dispatch_input(self, etype, me):
        '''This function is called by :meth:`EventLoopBase.dispatch_input()`
        when we want to dispatch an input event. The event is dispatched to
        all listeners and if grabbed, it's dispatched to grabbed widgets.
        '''
        # update available list
        if etype == 'begin':
            self.me_list.append(me)
        elif etype == 'end':
            if me in self.me_list:
                self.me_list.remove(me)
        # dispatch to listeners
        if not me.grab_exclusive_class:
            for listener in self.event_listeners:
                listener.dispatch('on_motion', etype, me)
        # dispatch grabbed touch
        if not me.is_touch:
            # Non-touch event must be handled by the event manager
            return
        me.grab_state = True
        for weak_widget in me.grab_list[:]:
            # weak_widget is a weak reference to widget
            wid = weak_widget()
            if wid is None:
                # object is gone, stop.
                me.grab_list.remove(weak_widget)
                continue
            root_window = wid.get_root_window()
            if wid != root_window and root_window is not None:
                me.push()
                try:
                    root_window.transform_motion_event_2d(me, wid)
                except AttributeError:
                    me.pop()
                    continue
            me.grab_current = wid
            wid._context.push()
            if etype == 'begin':
                # don't dispatch again touch in on_touch_down
                # a down event are nearly uniq here.
                # wid.dispatch('on_touch_down', touch)
                pass
            elif etype == 'update':
                if wid._context.sandbox:
                    with wid._context.sandbox:
                        wid.dispatch('on_touch_move', me)
                else:
                    wid.dispatch('on_touch_move', me)
            elif etype == 'end':
                if wid._context.sandbox:
                    with wid._context.sandbox:
                        wid.dispatch('on_touch_up', me)
                else:
                    wid.dispatch('on_touch_up', me)
            wid._context.pop()
            me.grab_current = None
            if wid != root_window and root_window is not None:
                me.pop()
        me.grab_state = False
        me.dispatch_done()

    def _dispatch_input(self, *ev):
        # remove the save event for the touch if exist
        if ev in self.input_events:
            self.input_events.remove(ev)
        self.input_events.append(ev)

    def dispatch_input(self):
        '''Called by :meth:`EventLoopBase.idle()` to read events from input
        providers, pass events to postproc, and dispatch final events.
        '''

        # first, acquire input events
        for provider in self.input_providers:
            provider.update(dispatch_fn=self._dispatch_input)

        # execute post-processing modules
        for mod in self.postproc_modules:
            self.input_events = mod.process(events=self.input_events)

        # real dispatch input
        input_events = self.input_events
        pop = input_events.pop
        post_dispatch_input = self.post_dispatch_input
        while input_events:
            post_dispatch_input(*pop(0))

    def mainloop(self):
        while not self.quit and self.status == 'started':
            try:
                self.idle()
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

    async def async_mainloop(self):
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

        Logger.info("Window: exiting mainloop and closing.")
        self.close()

    def idle(self):
        '''This function is called after every frame. By default:

           * it "ticks" the clock to the next frame.
           * it reads all input and dispatches events.
           * it dispatches `on_update`, `on_draw` and `on_flip` events to the
             window.
        '''

        # update dt
        Clock.tick()

        # read and dispatch input from providers
        if not self.quit:
            self.dispatch_input()

        # flush all the canvas operation
        if not self.quit:
            Builder.sync()

        # tick before draw
        if not self.quit:
            Clock.tick_draw()

        # flush all the canvas operation
        if not self.quit:
            Builder.sync()

        if not self.quit:
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

    async def async_idle(self):
        '''Identical to :meth:`idle`, but instead used when running
        within an async event loop.
        '''

        # update dt
        await Clock.async_tick()

        # read and dispatch input from providers
        if not self.quit:
            self.dispatch_input()

        # flush all the canvas operation
        if not self.quit:
            Builder.sync()

        # tick before draw
        if not self.quit:
            Clock.tick_draw()

        # flush all the canvas operation
        if not self.quit:
            Builder.sync()

        if not self.quit:
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

    def run(self):
        '''Main loop'''
        while not self.quit:
            self.idle()
        self.exit()

    def exit(self):
        '''Close the main loop and close the window.'''
        self.close()
        if self.window:
            self.window.close()

    def on_stop(self):
        '''Event handler for `on_stop` events which will be fired right
        after all input providers have been stopped.'''
        pass

    def on_pause(self):
        '''Event handler for `on_pause` which will be fired when
        the event loop is paused.'''
        pass

    def on_start(self):
        '''Event handler for `on_start` which will be fired right
        after all input providers have been started.'''
        pass


#: EventLoop instance
EventLoop = EventLoopBase()


def _runTouchApp_prepare(widget=None):
    from kivy.input import MotionEventFactory, kivy_postproc_modules

    # Ok, we got one widget, and we are not in embedded mode
    # so, user don't create the window, let's create it for him !
    if widget:
        EventLoop.ensure_window()

    # Instance all configured input
    for key, value in Config.items('input'):
        Logger.debug('Base: Create provider from %s' % (str(value)))

        # split value
        args = str(value).split(',', 1)
        if len(args) == 1:
            args.append('')
        provider_id, args = args
        provider = MotionEventFactory.get(provider_id)
        if provider is None:
            Logger.warning('Base: Unknown <%s> provider' % str(provider_id))
            continue

        # create provider
        p = provider(key, args)
        if p:
            EventLoop.add_input_provider(p, True)

    # add postproc modules
    for mod in list(kivy_postproc_modules.values()):
        EventLoop.add_postproc_module(mod)

    # add main widget
    if widget and EventLoop.window:
        if widget not in EventLoop.window.children:
            EventLoop.window.add_widget(widget)

    # start event loop
    Logger.info('Base: Start application main loop')
    EventLoop.start()

    # remove presplash on the next frame
    if platform == 'android':
        Clock.schedule_once(EventLoop.remove_android_splash)

    # in non-embedded mode, there are 2 issues
    #
    # 1. if user created a window, call the mainloop from window.
    #    This is due to glut, it need to be called with
    #    glutMainLoop(). Only FreeGLUT got a gluMainLoopEvent().
    #    So, we are executing the dispatching function inside
    #    a redisplay event.
    #
    # 2. if no window is created, we are dispatching event loop
    #    ourself (previous behavior.)
    #


def runTouchApp(widget=None, embedded=False):
    '''Static main function that starts the application loop.
    You can access some magic via the following arguments:

    See :mod:`kivy.app` for example usage.

    :Parameters:
        `<empty>`
            To make dispatching work, you need at least one
            input listener. If not, application will leave.
            (MTWindow act as an input listener)

        `widget`
            If you pass only a widget, a MTWindow will be created
            and your widget will be added to the window as the root
            widget.

        `embedded`
            No event dispatching is done. This will be your job.

        `widget + embedded`
            No event dispatching is done. This will be your job but
            we try to get the window (must be created by you beforehand)
            and add the widget to it. Very useful for embedding Kivy
            in another toolkit. (like Qt, check kivy-designed)

    '''
    _runTouchApp_prepare(widget=widget)

    # we are in embedded mode, don't do dispatching.
    if embedded:
        return

    try:
        EventLoop.mainloop()
    finally:
        stopTouchApp()


async def async_runTouchApp(widget=None, embedded=False, async_lib=None):
    '''Identical to :func:`runTouchApp` but instead it is a coroutine
    that can be run in an existing async event loop.

    ``async_lib`` is the async library to use. See :mod:`kivy.app` for details
    and example usage.

    .. versionadded:: 2.0.0
    '''
    if async_lib is not None:
        Clock.init_async_lib(async_lib)
    _runTouchApp_prepare(widget=widget)

    # we are in embedded mode, don't do dispatching.
    if embedded:
        return

    try:
        await EventLoop.async_mainloop()
    finally:
        stopTouchApp()


def stopTouchApp():
    '''Stop the current application by leaving the main loop.

    See :mod:`kivy.app` for example usage.
    '''
    if EventLoop is None:
        return
    if EventLoop.status in ('stopped', 'closed'):
        return
    if EventLoop.status != 'started':
        if not EventLoop.stopping:
            EventLoop.stopping = True
            Clock.schedule_once(lambda dt: stopTouchApp(), 0)
        return
    Logger.info('Base: Leaving application in progress...')
    EventLoop.close()

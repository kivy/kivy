# pylint: disable=W0611
'''
Kivy Base
=========

This module contains core Kivy functionality and is not intended for end users.
Feel free to look though it, but calling any of these methods directly may well
result in unpredictable behavior.

Event loop management
---------------------

'''

__all__ = (
    'EventLoop',
    'EventLoopBase',
    'ExceptionHandler',
    'ExceptionManagerBase',
    'ExceptionManager',
    'runTouchApp',
    'stopTouchApp',
)

import sys
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
                Logger.exception('Exception catched by ExceptionHandler')
                return ExceptionManager.PASS

        ExceptionManager.add_handler(E())

    All exceptions will be set to PASS, and logged to the console!
    '''

    def __init__(self):
        pass

    def handle_exception(self, exception):
        '''Handle one exception, defaults to returning
        ExceptionManager.STOP.
        '''
        return ExceptionManager.RAISE


class ExceptionManagerBase:
    '''ExceptionManager manages exceptions handlers.'''

    RAISE = 0
    PASS = 1

    def __init__(self):
        self.handlers = []
        self.policy = ExceptionManagerBase.RAISE

    def add_handler(self, cls):
        '''Add a new exception handler to the stack.'''
        if cls not in self.handlers:
            self.handlers.append(cls)

    def remove_handler(self, cls):
        '''Remove a exception handler from the stack.'''
        if cls in self.handlers:
            self.handlers.remove(cls)

    def handle_exception(self, inst):
        '''Called when an exception occurred in the runTouchApp() main loop.'''
        ret = self.policy
        for handler in self.handlers:
            r = handler.handle_exception(inst)
            if r == ExceptionManagerBase.PASS:
                ret = r
        return ret


#: Instance of a :class:`ExceptionManagerBase` implementation.
ExceptionManager = register_context('ExceptionManager', ExceptionManagerBase)


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
        '''
        if provider in self.input_providers:
            self.input_providers.remove(provider)

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
        '''Must be called only once before run().
        This starts all configured input providers.'''
        self.status = 'started'
        self.quit = False
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
        EventLoop.add_stop_callback().'''

        # XXX stop in reverse order that we started them!! (like push
        # pop), very important because e.g. wm_touch and WM_PEN both
        # store old window proc and the restore, if order is messed big
        # problem happens, crashing badly without error
        for provider in reversed(self.input_providers[:]):
            provider.stop()
            if provider in self.input_providers_autoremove:
                self.input_providers_autoremove.remove(provider)
                self.input_providers.remove(provider)

        # ensure any restart will not break anything later.
        self.input_events = []

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
            Logger.error(
                'Base: Failed to import "android" module. '
                'Could not remove android presplash.')
            return

    def post_dispatch_input(self, etype, me):
        '''This function is called by dispatch_input() when we want to dispatch
        an input event. The event is dispatched to all listeners and if
        grabbed, it's dispatched to grabbed widgets.
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
        me.grab_state = True
        for _wid in me.grab_list[:]:

            # it's a weakref, call it!
            wid = _wid()
            if wid is None:
                # object is gone, stop.
                me.grab_list.remove(_wid)
                continue

            root_window = wid.get_root_window()
            if wid != root_window and root_window is not None:
                me.push()
                w, h = root_window.system_size
                if platform == 'ios' or root_window._density != 1:
                    w, h = root_window.size
                kheight = root_window.keyboard_height
                smode = root_window.softinput_mode
                me.scale_for_screen(w, h, rotation=root_window.rotation,
                                    smode=smode, kheight=kheight)
                parent = wid.parent
                # and do to_local until the widget
                try:
                    if parent:
                        me.apply_transform_2d(parent.to_widget)
                    else:
                        me.apply_transform_2d(wid.to_widget)
                        me.apply_transform_2d(wid.to_parent)
                except AttributeError:
                    # when using inner window, an app have grab the touch
                    # but app is removed. the touch can't access
                    # to one of the parent. (i.e, self.parent will be None)
                    # and BAM the bug happen.
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

    def _dispatch_input(self, *ev):
        # remove the save event for the touch if exist
        if ev in self.input_events:
            self.input_events.remove(ev)
        self.input_events.append(ev)

    def dispatch_input(self):
        '''Called by idle() to read events from input providers, pass events to
        postproc, and dispatch final events.
        '''

        # first, aquire input events
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


def _run_mainloop():
    '''If no window has been created, this will be the executed mainloop.'''
    while True:
        try:
            EventLoop.run()
            stopTouchApp()
            break
        except BaseException as inst:
            # use exception manager first
            r = ExceptionManager.handle_exception(inst)
            if r == ExceptionManager.RAISE:
                stopTouchApp()
                raise
            else:
                pass


def runTouchApp(widget=None, slave=False):
    '''Static main function that starts the application loop.
    You can access some magic via the following arguments:

    :Parameters:
        `<empty>`
            To make dispatching work, you need at least one
            input listener. If not, application will leave.
            (MTWindow act as an input listener)

        `widget`
            If you pass only a widget, a MTWindow will be created
            and your widget will be added to the window as the root
            widget.

        `slave`
            No event dispatching is done. This will be your job.

        `widget + slave`
            No event dispatching is done. This will be your job but
            we try to get the window (must be created by you beforehand)
            and add the widget to it. Very useful for embedding Kivy
            in another toolkit. (like Qt, check kivy-designed)

    '''

    from kivy.input import MotionEventFactory, kivy_postproc_modules

    # Ok, we got one widget, and we are not in slave mode
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

    # we are in a slave mode, don't do dispatching.
    if slave:
        return

    # in non-slave mode, they are 2 issues
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
    try:
        if EventLoop.window is None:
            _run_mainloop()
        else:
            EventLoop.window.mainloop()
    finally:
        stopTouchApp()


def stopTouchApp():
    '''Stop the current application by leaving the main loop'''
    if EventLoop is None:
        return
    if EventLoop.status != 'started':
        return
    Logger.info('Base: Leaving application in progress...')
    EventLoop.close()

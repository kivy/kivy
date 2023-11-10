'''
Support
=======

Activate other frameworks/toolkits inside the kivy event loop.

'''

__all__ = ('install_gobject_iteration', 'install_twisted_reactor',
           'uninstall_twisted_reactor', 'install_android')


def install_gobject_iteration():
    '''Import and install gobject context iteration inside our event loop.
    This is used as soon as gobject is used (like gstreamer).
    '''

    from kivy.clock import Clock

    try:
        from gi.repository import GObject as gobject
    except ImportError:
        import gobject

    if hasattr(gobject, '_gobject_already_installed'):
        # already installed, don't do it twice.
        return

    gobject._gobject_already_installed = True

    # get gobject mainloop / context
    loop = gobject.MainLoop()
    gobject.threads_init()
    context = loop.get_context()

    # schedule the iteration each frame
    def _gobject_iteration(*largs):
        # XXX we need to loop over context here, otherwise, we might have a lag
        loop = 0
        while context.pending() and loop < 10:
            context.iteration(False)
            loop += 1
    Clock.schedule_interval(_gobject_iteration, 0)


# -----------------------------------------------------------------------------
# Android support
# -----------------------------------------------------------------------------

g_android_redraw_count = 0
_redraw_event = None


def _android_ask_redraw(*largs):
    # after wakeup, we need to redraw more than once, otherwise we get a
    # black screen
    global g_android_redraw_count
    from kivy.core.window import Window
    Window.canvas.ask_update()
    g_android_redraw_count -= 1
    if g_android_redraw_count < 0:
        return False


def install_android():
    '''Install hooks for the android platform.

    * Automatically sleep when the device is paused.
    * Automatically kill the application when the return key is pressed.
    '''
    try:
        import android
    except ImportError:
        print('Android lib is missing, cannot install android hooks')
        return

    from kivy.clock import Clock
    from kivy.logger import Logger
    import pygame

    Logger.info('Support: Android install hooks')

    # Init the library
    android.init()
    android.map_key(android.KEYCODE_MENU, pygame.K_MENU)
    android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)

    # Check if android should be paused or not.
    # If pause is requested, just leave the app.
    def android_check_pause(*largs):
        # do nothing until android asks for it.
        if not android.check_pause():
            return

        from kivy.app import App
        from kivy.base import stopTouchApp
        from kivy.logger import Logger
        from kivy.core.window import Window
        global g_android_redraw_count, _redraw_event

        # try to get the current running application
        Logger.info('Android: Must go into sleep mode, check the app')
        app = App.get_running_app()

        # no running application, stop our loop.
        if app is None:
            Logger.info('Android: No app running, stop everything.')
            stopTouchApp()
            return

        # try to go to pause mode
        if app.dispatch('on_pause'):
            Logger.info('Android: App paused, now wait for resume.')

            # app goes in pause mode, wait.
            android.wait_for_resume()

            # is it a stop or resume ?
            if android.check_stop():
                # app must stop
                Logger.info('Android: Android wants to close our app.')
                stopTouchApp()
            else:
                # app resuming now !
                Logger.info('Android: Android has resumed, resume the app.')
                app.dispatch('on_resume')
                Window.canvas.ask_update()
                g_android_redraw_count = 25  # 5 frames/seconds for 5 seconds
                if _redraw_event is None:
                    _redraw_event = Clock.schedule_interval(
                        _android_ask_redraw, 1 / 5)
                else:
                    _redraw_event.cancel()
                    _redraw_event()
                Logger.info('Android: App resume completed.')

        # app doesn't support pause mode, just stop it.
        else:
            Logger.info('Android: App doesn\'t support pause mode, stop.')
            stopTouchApp()

    Clock.schedule_interval(android_check_pause, 0)


_twisted_reactor_stopper = None
_twisted_reactor_work = None


def install_twisted_reactor(**kwargs):
    '''Installs a threaded twisted reactor, which will schedule one
    reactor iteration before the next frame only when twisted needs
    to do some work.

    Any arguments or keyword arguments passed to this function will be
    passed on the threadedselect reactors interleave function. These
    are the arguments one would usually pass to twisted's reactor.startRunning.

    Unlike the default twisted reactor, the installed reactor will not handle
    any signals unless you set the 'installSignalHandlers' keyword argument
    to 1 explicitly. This is done to allow kivy to handle the signals as
    usual unless you specifically want the twisted reactor to handle the
    signals (e.g. SIGINT).

    .. note::
        Twisted is not included in iOS build by default. To use it on iOS,
        put the twisted distribution (and zope.interface dependency) in your
        application directory.
    '''

    import twisted

    # prevent installing more than once
    if hasattr(twisted, '_kivy_twisted_reactor_installed'):
        return
    twisted._kivy_twisted_reactor_installed = True

    # don't let twisted handle signals, unless specifically requested
    kwargs.setdefault('installSignalHandlers', 0)

    # install threaded-select reactor, to use with own event loop
    from twisted.internet import _threadedselect
    _threadedselect.install()

    # now we can import twisted reactor as usual
    from twisted.internet import reactor
    from twisted.internet.error import ReactorNotRunning

    from collections import deque
    from kivy.base import EventLoop
    from kivy.logger import Logger
    from kivy.clock import Clock

    # will hold callbacks to twisted callbacks
    q = deque()

    # twisted will call the wake function when it needs to do work
    def reactor_wake(twisted_loop_next):
        '''Wakeup the twisted reactor to start processing the task queue
        '''

        Logger.trace("Support: twisted wakeup call to schedule task")
        q.append(twisted_loop_next)

    # called every frame, to process the reactors work in main thread
    def reactor_work(*args):
        '''Process the twisted reactor task queue
        '''
        Logger.trace("Support: processing twisted task queue")
        while len(q):
            q.popleft()()
    global _twisted_reactor_work
    _twisted_reactor_work = reactor_work

    # start the reactor, by telling twisted how to wake, and process
    def reactor_start(*args):
        '''Start the twisted reactor main loop
        '''
        Logger.info("Support: Starting twisted reactor")
        reactor.interleave(reactor_wake, **kwargs)
        Clock.schedule_interval(reactor_work, 0)

    # make sure twisted reactor is shutdown if eventloop exists
    def reactor_stop(*args):
        '''Shutdown the twisted reactor main loop
        '''
        if reactor.threadpool:
            Logger.info("Support: Stopping twisted threads")
            reactor.threadpool.stop()
        Logger.info("Support: Shutting down twisted reactor")
        reactor._mainLoopShutdown()
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass

        import sys
        sys.modules.pop('twisted.internet.reactor', None)

    global _twisted_reactor_stopper
    _twisted_reactor_stopper = reactor_stop

    # start and stop the reactor along with kivy EventLoop
    Clock.schedule_once(reactor_start, 0)
    EventLoop.bind(on_stop=reactor_stop)


def uninstall_twisted_reactor():
    '''Uninstalls the Kivy's threaded Twisted Reactor. No more Twisted
    tasks will run after this got called. Use this to clean the
    `twisted.internet.reactor` .

    .. versionadded:: 1.9.0
    '''

    import twisted

    # prevent uninstalling more than once
    if not hasattr(twisted, '_kivy_twisted_reactor_installed'):
        return

    from kivy.base import EventLoop

    global _twisted_reactor_stopper
    _twisted_reactor_stopper()
    EventLoop.unbind(on_stop=_twisted_reactor_stopper)

    del twisted._kivy_twisted_reactor_installed

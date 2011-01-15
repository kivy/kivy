'''
Support: activate other framework/toolkit inside our event loop
'''

__all__ = ('install_gobject_iteration', 'install_android')


def install_gobject_iteration():
    '''Import and install gobject context iteration inside our event loop.
    This is used as soon as gobject is used (like gstreamer)
    '''

    from kivy.clock import Clock
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
        if context.pending():
            context.iteration(False)
    Clock.schedule_interval(_gobject_iteration, 0)

def install_android():
    '''Install hooks for android platform.

    * Automaticly sleep when the device is paused
    * Auto kill the application is the return key is hitted
    '''
    try:
        import android
    except ImportError:
        print 'Android lib is missing, cannot install android hooks'
        return

    print '==========+> Android install hooks'

    def android_check_pause(*largs):
        if not android.check_pause():
            return
        from kivy.base import stopTouchApp
        stopTouchApp()
        #android.wait_for_resume()

    from kivy.clock import Clock
    Clock.schedule_interval(android_check_pause, 0)


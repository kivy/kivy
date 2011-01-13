'''
Support: activate other framework/toolkit inside our event loop
'''

__all__ = ('install_gobject_iteration', )


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

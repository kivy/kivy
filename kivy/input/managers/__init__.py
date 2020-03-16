from kivy.utils import platform


class EventManagerBase(object):

    def __init__(self, **kwargs):
        self.type_name = None
        self.event_loop = None

    def update(self, etype, me):
        pass

    def dispatch(self, *args):
        pass

    def transform_grabbed_event(self, root_window, widget, me):
        w, h = root_window.system_size
        if platform == 'ios' or root_window._density != 1:
            w, h = root_window.size
        kheight = root_window.keyboard_height
        smode = root_window.softinput_mode
        me.scale_for_screen(w, h, rotation=root_window.rotation,
                            smode=smode, kheight=kheight)
        parent = widget.parent
        try:
            if parent:
                me.apply_transform_2d(parent.to_widget)
            else:
                me.apply_transform_2d(widget.to_widget)
                me.apply_transform_2d(widget.to_parent)
        except AttributeError:
            # when using inner window, an app have grab the touch
            # but app is removed. the touch can't access
            # to one of the parent. (i.e, self.parent will be None)
            # and BAM the bug happen.
            raise
        return me

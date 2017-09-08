'''
Window manager
==============

The kivy window manager is a compositing window manager that exposes an
interface for creating Kivy widgets from X windows, which can be sized and
positioned according to kivy layouts.

'''

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.window import Window as KivyWindow

import select

try:
    import Xlib.display
    import Xlib.error
    import Xlib.protocol.event
    import Xlib.X
except ModuleNotFoundError:
    Logger.warning('WindowMgr: Unable to import Xlib, please install it with "pip install python-xlib"')


class Window(Widget):
    def on_size(self):
        pass

    def on_pos(self):
        pass


class BaseWindowManager(EventDispatcher):
    windows = ListProperty([])

    event_mapping = {
            'CreateNotify': 'on_create_notify',
            'DestroyNotify': 'on_destroy_notify',
            'UnmapNotify': 'on_unmap_notify',
            'MapNotify': 'on_map_notify',
            'MapRequest': 'on_map_request',
            'ReparentNotify': 'on_reparent_notify',
            'ConfigureNotify': 'on_configure_notify',
            'ConfigureRequest': 'on_configure_request',
        }

    def __init__(self, **kwargs):
        super(BaseWindowManager, self).__init__()

        # Convert event strings to X protocol values
        self.event_mapping = {
            getattr(Xlib.X, event): handler
            for event, handler in self.event_mapping.items()
        }

        [self.register_event_type(event)
            for event in self.event_mapping.values()]

        self.connect()

        self.bind(on_start=self.setup_wm)

        Clock.schedule_interval(lambda dt: self.poll_events(), 0)

    def connect(self):
        try:
            self.display = Xlib.display.Display()
        except Xlib.error.DisplayConnectionError:
            Logger.error('WindowMgr: Unable to connect to X server')
            raise

    def setup_wm(self, *args):
        self.root_win = self.display.screen().root

        event_mask = Xlib.X.SubstructureNotifyMask \
                   | Xlib.X.SubstructureRedirectMask

        ec = Xlib.error.CatchError(Xlib.error.BadAccess)
        self.root_win.change_attributes(event_mask=event_mask, onerror=ec)
        self.display.sync()

        if ec.get_error():
            Logger.error('WindowMgr: Unable to create window manager, another one is running')

    def poll_events(self):
        readable, w, e = select.select([self.display], [], [], 0)

        if not readable:
            return
        elif self.display in readable:
            num_events = self.display.pending_events()
            Logger.info
            for i in range(num_events):
                self.handle_event(self.display.next_event())

    def handle_event(self, event):
        try:
            self.dispatch(self.event_mapping[event.type], event)
        except Xlib.error.BadWindow:
            # TODO: Handle BadWindow
            pass

    def on_create_notify(self, event):
        pass

    def on_destroy_notify(self, event):
        pass

    def on_unmap_notify(self, event):
        pass

    def on_map_notify(self, event):
        pass

    def on_map_request(self, event):
        pass

    def on_reparent_notify(self, event):
        pass

    def on_configure_notify(self, event):
        pass

    def on_configure_request(self, event):
        pass

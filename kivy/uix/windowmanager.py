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
    from Xlib.ext.composite import RedirectAutomatic
except ModuleNotFoundError:
    Logger.warning('WindowMgr: Unable to import Xlib, please install it with "pip install python-xlib"')


class XWindow(Widget):
    texture = ObjectProperty(None)

    def __init__(self, manager, window, **kwargs):
        super(XWindow, self).__init__(**kwargs)

        self.manager = manager

        self.pixmap = None
        self._window = window

        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # HACK: invalidate the pixmap every couple of seconds to update the
        # texture. This is simply to ease development before adding support for
        # damage and fixes
        Clock.schedule_interval(lambda dt: self.on_window_map(), 2)

        self.register_event_type('on_window_map')
        self.register_event_type('on_window_resize')

    @property
    def name(self):
        return self._window.get_wm_name()

    def on_window_map(self):
        self.invalidate_pixmap()

    def on_window_resize(self):
        self.invalidate_pixmap()

    def invalidate_pixmap(self):
        self.bind_texture()
        self.redraw()

    def bind_texture(self):
        if self.pixmap:
            self.pixmap.free()

        self.pixmap = self._window.composite_name_window_pixmap()
        self.manager.display.sync()

        if self.texture:
            self.texture.release_pixmap()

        # TODO: Get window geometry, and create a texture based on the actual
        # window size. There appears to be an issue with displaying NPOT
        # textures.
        self.texture = Texture.create_from_pixmap(self._window.id, (256, 256))

    def redraw(self, *args):
        self.rect.texture = self.texture
        self.rect.size = self.texture.size
        self.rect.pos = self.pos

    def on_parent(self, *args):
        if self.parent:
            self._window.map()
        else:
            self._window.unmap()

class BaseWindowManager(App):
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

class CompositingWindowManager(BaseWindowManager):
    required_extensions = ['Composite']

    def check_extensions(self, extensions):
        for extension in extensions:
            if self.display.has_extension(extension):
                Logger.info('WindowMgr: has extension {}'.format(extension))
            else:
                Logger.error('WindowMgr: no support for extension {}'.format(extension))

    def setup_wm(self, *args):
        self.check_extensions(self.required_extensions)

        super(CompositingWindowManager, self).setup_wm()
        self.root_win.composite_redirect_subwindows(RedirectAutomatic)
        self.overlay_window = self.root_win.composite_get_overlay_window().overlay_window
        self.display.sync()

        app = App.get_running_app()
        for window in self.root_win.query_tree().children:
            if window.id == KivyWindow.get_xwindow():
                Logger.info('WindowMgr: Found kivy window')
                window.reparent(self.overlay_window, x=0, y=0)
                window.map()
                self.display.sync()
                break


class KivyWindowManager(CompositingWindowManager):
    windows = DictProperty([])
    window_callbacks = DictProperty({'name': {}, 'id': {}})

    def _add_child(self, window):
        ''' Creates an XWindow object that can be retrieved and used as a widget by the main app
        '''
        if window.id not in self.windows:
            self.windows[window.id] = XWindow(self, window)
            print(f'Created XWindow from <{window.get_wm_name()}>')

        default_window_callback = self.window_callbacks.get(None)
        if default_window_callback:
            default_window_callback(self.windows[window.id])
            print('Executed default callback')

        id_callback = self.window_callbacks['id'].get(window.id)
        if id_callback:
            id_callback(self.windows[window.id])
            print('Executed id callback')

        name_callback = self.window_callbacks['name'].get(window.get_wm_name())
        if name_callback:
            name_callback(self.windows[window.id])
            print('Executed named callback')

    def _remove_child(self, window):
        ''' Remove a child window
        '''
        if window.id in self.windows:
            del self.windows[window.id]

    def add_window_callback(self, cb, name=None, id=None):
        if name:
            self.window_callbacks['name'][name] = cb
        elif id:
            self.window_callbacks['id'][id] = cb
        else:
            self.window_callbacks[None] = cb

    def get_window_by_name(self, name):
        for xid, window in self.windows.items():
            if window.get_wm_name() == name:
                return window
        return None

    def get_window_by_xid(self, xid):
        return self.windows.get(xid)

    def on_create_notify(self, event):
        app = App.get_running_app()

        # Don't create a child for the Kivy window
        if event.window.id == KivyWindow.get_xwindow():
            return

        self._add_child(event.window)

        Logger.info(f'Created window: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_create_notify(event)

    def on_destroy_notify(self, event):
        Logger.info(f'Destroyed window: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_destroy_notify(event)

    def on_unmap_notify(self, event):
        Logger.info(f'Unmap notify: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_unmap_notify(event)

    def on_map_notify(self, event):
        if event.window.id in self.windows:
            self.windows[event.window.id].dispatch('on_window_map')

        Logger.info(f'Map notify: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_map_notify(event)

    def on_map_request(self, event):
        Logger.info(f'Map request: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_map_request(event)

    def on_reparent_notify(self, event):
        Logger.info(f'Reparented window: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_reparent_notify(event)

    def on_reparent_request(self, event):
        Logger.info(f'Reparent request: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_reparent_request(event)

    def on_configure_notify(self):
        if event.window.id in self.windows:
            # TODO: Check if the window was actually resized
            self.windows[event.window.id].dispatch('on_window_resize')

        Logger.info(f'Configure notify: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_configure_notify(event)

    def on_configure_request(self, event):
        Logger.info(f'Configure request: {event}, name: {event.window.get_wm_name()}')
        super(KivyWindowManager, self).on_configure_request(event)


'''
Window: Create a GL Window

For windowing system, we try to use the best windowing system available for
your system. Actually, theses libraries are handled :

    * PyGame (wrapper around SDL)
    * GLUT (last solution, really buggy :/)

'''

__all__ = ('WindowBase', 'Window')

from kivy.core import core_select_lib
from kivy.config import Config
from kivy.logger import Logger
from kivy.base import EventLoop
from kivy.modules import Modules
from kivy.event import EventDispatcher

class WindowBase(EventDispatcher):
    '''WindowBase is a abstract window widget, for any window implementation.

    .. warning::

        The parameters are not working in normal case. Because at import, Kivy
        create a default OpenGL window, to add the ability to use OpenGL
        directives, texture creation.. before creating MTWindow.
        If you don't like this behavior, you can include before the very first
        import of Kivy ::

            import os
            os.environ['KIVY_SHADOW'] = '0'
            from kivy import *

        This will forbid Kivy to create the default window !


    :Parameters:
        `fps`: int, default to 0
            Maximum FPS allowed. If 0, fps will be not limited
        `fullscreen`: bool
            Make window as fullscreen
        `width`: int
            Width of window
        `height`: int
            Height of window
        `vsync`: bool
            Vsync window
    '''

    __instance = None
    __initialized = False

    def __new__(cls, **kwargs):
        if cls.__instance is None:
            cls.__instance = EventDispatcher.__new__(cls)
        return cls.__instance

    def __init__(self, **kwargs):

        kwargs.setdefault('force', False)
        kwargs.setdefault('config', None)
        kwargs.setdefault('show_fps', False)

        # don't init window 2 times,
        # except if force is specified
        if self.__initialized and not kwargs.get('force'):
            return

        super(WindowBase, self).__init__()

        # init privates
        self._modifiers = []
        self._size = (0, 0)
        self._rotation = 0

        # event subsystem
        self.register_event_type('on_draw')
        self.register_event_type('on_flip')
        self.register_event_type('on_rotate')
        self.register_event_type('on_resize')
        self.register_event_type('on_close')
        self.register_event_type('on_touch_down')
        self.register_event_type('on_touch_move')
        self.register_event_type('on_touch_up')
        self.register_event_type('on_mouse_down')
        self.register_event_type('on_mouse_move')
        self.register_event_type('on_mouse_up')
        self.register_event_type('on_keyboard')
        self.register_event_type('on_key_down')
        self.register_event_type('on_key_up')

        self.children = []
        self.parent = self
        #self.visible = True

        # add view
        if 'view' in kwargs:
            self.add_widget(kwargs.get('view'))

        # get window params, user options before config option
        params = {}

        if 'fullscreen' in kwargs:
            params['fullscreen'] = kwargs.get('fullscreen')
        else:
            params['fullscreen'] = Config.get('graphics', 'fullscreen')
            if params['fullscreen'] not in ('auto', 'fake'):
                params['fullscreen'] = params['fullscreen'].lower() in \
                    ('true', '1', 'yes', 'yup')

        if 'width' in kwargs:
            params['width'] = kwargs.get('width')
        else:
            params['width'] = Config.getint('graphics', 'width')

        if 'height' in kwargs:
            params['height'] = kwargs.get('height')
        else:
            params['height'] = Config.getint('graphics', 'height')

        if 'vsync' in kwargs:
            params['vsync'] = kwargs.get('vsync')
        else:
            params['vsync'] = Config.getint('graphics', 'vsync')

        if 'fps' in kwargs:
            params['fps'] = kwargs.get('fps')
        else:
            params['fps'] = Config.getint('graphics', 'fps')

        if 'rotation' in kwargs:
            params['rotation'] = kwargs.get('rotation')
        else:
            params['rotation'] = Config.getint('graphics', 'rotation')

        params['position'] = Config.get(
            'graphics', 'position', 'auto')
        if 'top' in kwargs:
            params['position'] = 'custom'
            params['top'] = kwargs.get('top')
        else:
            params['top'] = Config.getint('graphics', 'top')

        if 'left' in kwargs:
            params['position'] = 'custom'
            params['left'] = kwargs.get('left')
        else:
            params['left'] = Config.getint('graphics', 'left')

        # show fps if asked
        self.show_fps = kwargs.get('show_fps')
        if Config.getboolean('kivy', 'show_fps'):
            self.show_fps = True

        # configure the window
        self.create_window(params)

        # create the canvas
        from kivy.graphics import Canvas
        self.canvas = Canvas()

        # attach modules + listener event
        Modules.register_window(self)
        EventLoop.set_window(self)
        EventLoop.add_event_listener(self)

        # mark as initialized
        self.__initialized = True

    def toggle_fullscreen(self):
        '''Toggle fullscreen on window'''
        pass

    def close(self):
        '''Close the window'''
        pass

    def create_window(self, params):
        '''Will create the main window and configure it'''
        pass

    def on_flip(self):
        '''Flip between buffers (event)'''
        self.flip()

    def flip(self):
        '''Flip between buffers'''
        pass

    def _get_modifiers(self):
        return self._modifiers
    modifiers = property(_get_modifiers)

    def _get_size(self):
        r = self._rotation
        w, h = self._size
        if r == 0 or r == 180:
            return w, h
        return h, w
    def _set_size(self, size):
        if super(WindowBase, self)._set_size(size):
            Logger.debug('Window: Resize window to %s' % str(self.size))
            self.dispatch('on_resize', *size)
            return True
        return False
    size = property(_get_size, _set_size,
        doc='''Rotated size of the window''')

    # make some property read-only
    @property
    def width(self):
        '''Rotated window width'''
        r = self._rotation
        if r == 0 or r == 180:
            return self._size[0]
        return self._size[1]
    @property
    def height(self):
        '''Rotated window height'''
        r = self._rotation
        if r == 0 or r == 180:
            return self._size[1]
        return self._size[0]
    @property
    def center(self):
        '''Rotated window center'''
        return self.width / 2., self.height / 2.

    def add_widget(self, w):
        '''Add a widget on window'''
        self.children.append(w)
        w.parent = self
        self.canvas.add(w.canvas)

    def remove_widget(self, w):
        '''Remove a widget from window'''
        if not w in self.children:
            return
        self.children.remove(w)
        w.parent = None
        self.canvas.remove_canvas(w.canvas)

    def clear(self):
        '''Clear the window with background color'''
        # XXX FIXME use late binding
        from kivy.core.gl import glClearColor, glClear, GL_COLOR_BUFFER_BIT, \
            GL_DEPTH_BUFFER_BIT
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def to_widget(self, x, y, initial=True, relative=False):
        return (x, y)

    def to_window(self, x, y, initial=True, relative=False):
        return (x, y)

    def get_root_window(self):
        return self

    def get_parent_window(self):
        return self

    def get_parent_layout(self):
        return None

    def on_draw(self):
        self.clear()
        self.canvas.draw()

    def on_touch_down(self, touch):
        '''Event called when a touch is down'''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in reversed(self.children[:]):
            if w.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Event called when a touch move'''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in reversed(self.children[:]):
            if w.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Event called when a touch up'''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in reversed(self.children[:]):
            if w.dispatch('on_touch_up', touch):
                return True

    def on_resize(self, width, height):
        '''Event called when the window is resized'''
        self.update_viewport()

    def update_viewport(self):
        # XXX FIXME
        from kivy.core.gl import *
        #from kivy.graphics import GraphicContext
        from kivy.lib.transformations import clip_matrix

        #context = GraphicContext.instance()
        #context.set('projection_mat', clip_matrix(0, self.width, 0, self.height, -1, 1))

        width, height = self.system_size
        w2 = width / 2.
        h2 = height / 2.

        # prepare the viewport
        glViewport(0, 0, width, height)

        # use the rotated size.
        # XXX FIXME fix rotation
        '''
        width, height = self.size
        w2 = width / 2.
        h2 = height / 2.
        glTranslatef(-w2, -h2, -500)

        # set the model view
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(w2, h2, 0)
        glRotatef(self._rotation, 0, 0, 1)
        glTranslatef(-w2, -h2, 0)
        '''

        # update window size
        for w in self.children:
            shw, shh = w.size_hint
            if shw and shh:
                w.size = shw * width, shh * height
            elif shw:
                w.width = shw * width
            elif shh:
                w.height = shh * height

    def _get_rotation(self):
        return self._rotation
    def _set_rotation(self, x):
        x = int(x % 360)
        if x == self._rotation:
            return
        if x not in (0, 90, 180, 270):
            raise ValueError('can rotate only 0,90,180,270 degrees')
        self._rotation = x
        self.dispatch('on_resize', *self.size)
        self.dispatch('on_rotate', x)
    rotation = property(_get_rotation, _set_rotation,
            'Get/set the window content rotation. Can be one of '
            '0, 90, 180, 270 degrees.')

    @property
    def system_size(self):
        '''Real size of the window, without taking care of the rotation
        '''
        return self._size

    def on_rotate(self, rotation):
        '''Event called when the screen have been rotated
        '''
        pass

    def on_close(self, *largs):
        '''Event called when the window is closed'''
        Modules.unregister_window(self)
        EventLoop.remove_event_listener(self)

    def on_mouse_down(self, x, y, button, modifiers):
        '''Event called when mouse is in action (press/release)'''
        pass

    def on_mouse_move(self, x, y, modifiers):
        '''Event called when mouse is moving, with buttons pressed'''
        pass

    def on_mouse_up(self, x, y, button, modifiers):
        '''Event called when mouse is moving, with buttons pressed'''
        pass

    def on_keyboard(self, key, scancode=None, unicode=None):
        '''Event called when keyboard is in action

        .. warning::
            Some providers can skip `scancode` or `unicode` !!
        '''
        pass

    def on_key_down(self, key, scancode=None, unicode=None):
        '''Event called when a key is down (same arguments as on_keyboard)'''
        pass

    def on_key_up(self, key, scancode=None, unicode=None):
        '''Event called when a key is up (same arguments as on_keyboard)'''
        pass


# Load the appropriate provider
Window = core_select_lib('window', (
    ('pygame', 'window_pygame', 'WindowPygame'),
))()


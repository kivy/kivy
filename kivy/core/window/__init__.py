'''
Window
======

Core class for create the default Kivy window. Kivy support only one window
creation. Don't try to create more than one.
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
        directives, texture creation.. before creating Window.
        If you don't like this behavior, you can include before the very first
        import of Kivy ::

            import os
            os.environ['KIVY_SHADOW'] = '0'

        This will forbid Kivy to create the default window !


    :Parameters:
        `fullscreen`: bool
            Make window as fullscreen
        `width`: int
            Width of window
        `height`: int
            Height of window

    :Events:
        `on_motion`: etype, motionevent
            Fired when a new :class:`~kivy.input.motionevent.MotionEvent` is
            dispatched
        `on_touch_down`:
            Fired when a new touch appear
        `on_touch_move`:
            Fired when an existing touch is moved
        `on_touch_down`:
            Fired when an existing touch disapear
        `on_draw`:
            Fired when the :class:`Window` is beeing drawed
        `on_flip`:
            Fired when the :class:`Window` GL surface is beeing flipped
        `on_rotate`: rotation
            Fired when the :class:`Window` is beeing rotated
        `on_close`:
            Fired when the :class:`Window` is closed
        `on_keyboard`: key, scancode, unicode, modifier
            Fired when the keyboard is in action
        `on_key_down`: key, scancode, unicode
            Fired when a key is down
        `on_key_up`: key, scancode, unicode
            Fired when a key is up
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

        # don't init window 2 times,
        # except if force is specified
        if self.__initialized and not kwargs.get('force'):
            return

        super(WindowBase, self).__init__()

        # init privates
        self._keyboard_callback = None
        self._modifiers = []
        self._size = (0, 0)
        self._rotation = 0
        self._clearcolor = [0, 0, 0, 0]

        # event subsystem
        self.register_event_type('on_draw')
        self.register_event_type('on_flip')
        self.register_event_type('on_rotate')
        self.register_event_type('on_resize')
        self.register_event_type('on_close')
        self.register_event_type('on_motion')
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

        # before creating the window
        import kivy.core.gl

        # configure the window
        self.params = params
        self.create_window()

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

    def create_window(self):
        '''Will create the main window and configure it.

        .. warning::
            This method is called automatically at runtime. If you call it, it
            will recreate a RenderContext and Canvas. This mean you'll have a
            new graphics tree, and the old one will be unusable.

            This method exist to permit the creation of a new OpenGL context
            AFTER closing the first one. (Like using runTouchApp() and
            stopTouchApp()).

            This method have been only tested in unittest environment, and will
            be not suitable for Applications.

            Again, don't use this method unless you know exactly what you are
            doing !
        '''
        from kivy.core.gl import init_gl
        init_gl()

        # create the render context and canvas
        from kivy.graphics import RenderContext, Canvas
        self.render_context = RenderContext()
        self.canvas = Canvas()
        self.render_context.add(self.canvas)

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

    def _get_clearcolor(self):
        return self._clearcolor

    def _set_clearcolor(self, value):
        if value is not None:
            if type(value) not in (list, tuple):
                raise Exception('Clearcolor must be a list or tuple')
            if len(value) != 4:
                raise Exception('Clearcolor must contain 4 values')
        self._clearcolor = value

    clearcolor = property(_get_clearcolor, _set_clearcolor,
        doc='''Color used to clear window::

            from kivy.core.window import Window

            # red background color
            Window.clearcolor = (1, 0, 0, 1)

            # don't clear background at all
            Window.clearcolor = None

        ''')

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

    def add_widget(self, widget):
        '''Add a widget on window'''
        self.children.append(widget)
        widget.parent = self
        self.canvas.add(widget.canvas)
        self.update_childsize([widget])

    def remove_widget(self, widget):
        '''Remove a widget from window
        '''
        if not widget in self.children:
            return
        self.children.remove(widget)
        self.canvas.remove(widget.canvas)
        widget.parent = None

    def clear(self):
        '''Clear the window with background color'''
        # XXX FIXME use late binding
        from kivy.graphics.opengl import glClearColor, glClear, \
            GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
        cc = self._clearcolor
        if cc is not None:
            glClearColor(*cc)
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
        self.render_context.draw()

    def on_motion(self, etype, me):
        '''Event called when a Motion Event is received.

        :Parameters:
            `etype`: str
                One of 'begin', 'update', 'end'
            `me`: :class:`~kivy.input.motionevent.MotionEvent`
                Motion Event currently dispatched
        '''
        if me.is_touch:
            if etype == 'begin':
                self.dispatch('on_touch_down', me)
            elif etype == 'update':
                self.dispatch('on_touch_move', me)
            elif etype == 'end':
                self.dispatch('on_touch_up', me)

    def on_touch_down(self, touch):
        '''Event called when a touch is down
        '''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in self.children[:]:
            if w.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Event called when a touch move
        '''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in self.children[:]:
            if w.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Event called when a touch up
        '''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in self.children[:]:
            if w.dispatch('on_touch_up', touch):
                return True

    def on_resize(self, width, height):
        '''Event called when the window is resized'''
        self.update_viewport()

    def update_viewport(self):
        from kivy.graphics.opengl import glViewport
        from kivy.graphics.transformation import Matrix

        width, height = self.system_size
        w2 = width / 2.
        h2 = height / 2.

        # prepare the viewport
        glViewport(0, 0, width, height)
        projection_mat = Matrix()
        projection_mat.view_clip(0.0, width, 0.0, height, -1.0, 1.0, 0)
        self.render_context['projection_mat'] = projection_mat

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

        self.update_childsize()

    def update_childsize(self, childs=None):
        width, height = self.system_size
        if childs is None:
            childs = self.children
        for w in childs:
            shw, shh = w.size_hint
            if shw and shh:
                w.size = shw * width, shh * height
            elif shw:
                w.width = shw * width
            elif shh:
                w.height = shh * height
            for key, value in w.pos_hint.iteritems():
                if key == 'x':
                    w.x = value * width
                elif key == 'right':
                    w.right = value * width
                elif key == 'y':
                    w.y = value * height
                elif key == 'top':
                    w.top = value * height
                elif key == 'center_x':
                    w.center_x = value * width
                elif key == 'center_y':
                    w.center_y = value * height

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

    def screenshot(self, name='screenshot%(counter)04d.jpg'):
        '''Save the actual displayed image in a file
        '''
        from os.path import join, exists
        from os import getcwd
        i = 0
        path = None
        while True:
            i += 1
            path = join(getcwd(), name % {'counter': i})
            if not exists(path):
                break
        return path

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

    def on_keyboard(self, key, scancode=None, unicode=None, modifier=None):
        '''Event called when keyboard is in action

        .. warning::
            Some providers may omit `scancode`, `unicode` and/or `modifier`!
        '''
        pass

    def on_key_down(self, key, scancode=None, unicode=None, modifier=None):
        '''Event called when a key is down (same arguments as on_keyboard)'''
        pass

    def on_key_up(self, key, scancode=None, unicode=None):
        '''Event called when a key is up (same arguments as on_keyboard)'''
        pass

    def request_keyboard(self, callback):
        '''.. versionadded:: 1.0.4


        Internal method for widget, to request the keyboard. This method is
        not intented to be used by end-user, however, if you want to use the
        real-keyboard (not virtual keyboard), you don't want to share it with
        another widget.

        A widget can request the keyboard, indicating a callback to call
        when the keyboard will be released (or taken by another widget).
        '''
        self.release_keyboard()
        self._keyboard_callback = callback
        return True

    def release_keyboard(self):
        '''.. versionadded:: 1.0.4


        Internal method for widget, to release the real-keyboard. Check
        :func:`request_keyboard` to understand how it works.
        '''
        if self._keyboard_callback:
            # this way will prevent possible recursion.
            callback = self._keyboard_callback
            self._keyboard_callback = None
            callback()
            return True


#: Instance of a :class:`WindowBase` implementation
Window = core_select_lib('window', (
    ('pygame', 'window_pygame', 'WindowPygame'),
), True)


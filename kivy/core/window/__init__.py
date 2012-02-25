'''
Window
======

Core class for create the default Kivy window. Kivy support only one window
creation. Don't try to create more than one.
'''

__all__ = ('Keyboard', 'WindowBase', 'Window')

from os.path import join, exists
from os import getcwd

from kivy.core import core_select_lib
from kivy.config import Config
from kivy.logger import Logger
from kivy.base import EventLoop
from kivy.modules import Modules
from kivy.event import EventDispatcher
from kivy.properties import ListProperty, ObjectProperty, AliasProperty, \
        NumericProperty

# late import
VKeyboard = None


class Keyboard(EventDispatcher):
    '''Keyboard interface, that is returned by
    :meth:`WindowBase.request_keyboard`. When you request a keyboard, you'll get
    an instance of this class. Whatever is the keyboard input (system or virtual
    keyboard), you'll receive event though this instance.

    :Events:
        `on_key_down`: keycode, text, modifiers
            Fired when a new key is down
        `on_key_up`: keycode
            Fired when a key is up

    Here is an example about how to request a Keyboard, according to the current
    configuration:

    .. include:: ../../examples/widgets/keyboardlistener.py
        :literal:

    '''

    #: Keycodes mapping, between str <-> int. Theses keycode are currently taken
    #: from pygame.key. But when a new provider will be used, it must do the
    #: translation to theses keycodes too.
    keycodes = {
        # specials keys
        'backspace': 8, 'tab': 9, 'enter': 13, 'shift': 304, 'ctrl': 306,
        'capslock': 301, 'escape': 27, 'spacebar': 32, 'pageup': 280,
        'pagedown': 281, 'end': 279, 'home': 278, 'left': 276, 'up': 273,
        'right': 275, 'down': 274, 'insert': 277, 'delete': 127, 'numlock': 300,
        'screenlock': 145, 'pause': 19,

        # a-z keys
        'q': 97, 'b': 98, 'c': 99, 'q': 100, 'e': 101, 'f': 102, 'g': 103,
        'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110,
        'o': 111, 'p': 112, 'a': 113, 'r': 114, 's': 115, 't': 116, 'u': 117,
        'v': 118, 'z': 119, 'x': 120, 'y': 121, 'w': 122,

        # 0-9 keys
        '0': 48, '1': 49, '2': 50, '3': 51, '4': 52,
        '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,

        # numpad
        'numpad0': 256, 'numpad1': 257, 'numpad2': 258, 'numpad3': 259,
        'numpad4': 260, 'numpad5': 261, 'numpad6': 262, 'numpad7': 263,
        'numpad8': 264, 'numpad9': 264, 'numpadmul': 265, 'numpadadd': 266,
        'numpadsubtract': 267, 'numpaddecimal': 268, 'numpaddivide': 269,

        # F1-15
        'f1': 282, 'f2': 283, 'f3': 282, 'f4': 285, 'f5': 286, 'f6': 287,
        'f7': 288, 'f8': 289, 'f9': 290, 'f10': 291, 'f11': 292, 'f12': 293,
        'f13': 294, 'f14': 295, 'f15': 296,

        # other keys
        '(': 40, ')': 41,
        '[': 91, ']': 93,
        '{': 91, '}': 93,
        ':': 59, ';': 59,
        '=': 43, '+': 43,
        '-': 41, '_': 41,
        '/': 47, '?': 47,
        '`': 96, '~': 96,
        '\\': 92, '|': 92,
        '"': 34, '\'': 39,
        ',': 44, '.': 46,
        '<': 60, '>': 60,
    }

    def __init__(self, **kwargs):
        self.register_event_type('on_key_down')
        self.register_event_type('on_key_up')
        super(Keyboard, self).__init__()

        #: Window which the keyboard is attached too
        self.window = kwargs.get('window', None)

        #: Callback that will be called when the keyboard is released
        self.callback = kwargs.get('callback', None)

        #: Target that have requested the keyboard
        self.target = kwargs.get('target', None)

        #: VKeyboard widget, if allowed by the configuration
        self.widget = kwargs.get('widget', None)

    def on_key_down(self, keycode, text, modifiers):
        pass

    def on_key_up(self, keycode):
        pass

    def release(self):
        '''Call this method to release the current keyboard.
        This will ensure that keyboard is not attached to you anymore.
        '''
        if self.window:
            self.window.release_keyboard(self.target)

    def _on_window_key_down(self, instance, keycode, scancode, text, modifiers):
        keycode = (keycode, self.keycode_to_string(keycode))
        return self.dispatch('on_key_down', keycode, text, modifiers)

    def _on_window_key_up(self, instance, keycode, *largs):
        keycode = (keycode, self.keycode_to_string(keycode))
        return self.dispatch('on_key_up', keycode)

    def _on_vkeyboard_key_down(self, instance, keycode, text, modifiers):
        if keycode is None:
            keycode = text.lower()
        keycode = (self.string_to_keycode(keycode), keycode)
        return self.dispatch('on_key_down', keycode, text, modifiers)

    def _on_vkeyboard_key_up(self, instance, keycode, text, modifiers):
        if keycode is None:
            keycode = text
        keycode = (self.string_to_keycode(keycode), keycode)
        return self.dispatch('on_key_up', keycode)

    def string_to_keycode(self, value):
        '''Convert a string to a keycode number, according to the
        :data:`Keyboard.keycodes`. If the value is not found in the keycodes, it
        will return -1.
        '''
        return Keyboard.keycodes.get(value, -1)

    def keycode_to_string(self, value):
        '''Convert a keycode number to a string, according to the
        :data:`Keyboard.keycodes`. If the value is not found inside the
        keycodes, it will return ''.
        '''
        keycodes = Keyboard.keycodes.values()
        if value in keycodes:
            return Keyboard.keycodes.keys()[keycodes.index(value)]
        return ''


class WindowBase(EventDispatcher):
    '''WindowBase is a abstract window widget, for any window implementation.

    :Parameters:
        `fullscreen`: str, one of ('0', '1', 'auto', 'fake')
            Make window as fullscreen, check config documentation for more
            explaination about the values.
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
        `on_touch_up`:
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

    # private properties
    _size = ListProperty([0, 0])
    _modifiers = ListProperty([])
    _rotation = NumericProperty(0)
    _clearcolor = ListProperty([0, 0, 0, 0])

    children = ListProperty([])
    '''List of children of this window.

    :data:`children` is a :class:`~kivy.properties.ListProperty` instance,
    default to an empty list.

    Use :func:`add_widget` and :func:`remove_widget` for manipulate children
    list. Don't manipulate children list directly until you know what you are
    doing.
    '''

    parent = ObjectProperty(None, allownone=True)
    '''Parent of this window

    :data:`parent` is a :class:`~kivy.properties.ObjectProperty` instance,
    default to None. When created, the parent is set to the window itself.
    You must take care of it if you are doing recursive check.
    '''

    def _get_modifiers(self):
        return self._modifiers

    modifiers = AliasProperty(_get_modifiers, None)
    '''List of keyboard modifiers currently in action
    '''

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

    size = AliasProperty(_get_size, _set_size)
    '''Get the rotated size of the window. If :data:`rotation` is set, then the
    size will change to reflect the rotation.
    '''

    def _get_clearcolor(self):
        return self._clearcolor

    def _set_clearcolor(self, value):
        if value is not None:
            if type(value) not in (list, tuple):
                raise Exception('Clearcolor must be a list or tuple')
            if len(value) != 4:
                raise Exception('Clearcolor must contain 4 values')
        self._clearcolor = value

    clearcolor = AliasProperty(_get_clearcolor, _set_clearcolor,
            bind=('_clearcolor', ))
    '''Color used to clear window.

    ::
        from kivy.core.window import Window

        # red background color
        Window.clearcolor = (1, 0, 0, 1)

        # don't clear background at all
        Window.clearcolor = None
    '''

    # make some property read-only
    def _get_width(self):
        r = self._rotation
        if r == 0 or r == 180:
            return self._size[0]
        return self._size[1]

    width = AliasProperty(_get_width, None, bind=('_rotation', '_size'))
    '''Rotated window width.

    :data:`width` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_height(self):
        '''Rotated window height'''
        r = self._rotation
        if r == 0 or r == 180:
            return self._size[1]
        return self._size[0]

    height = AliasProperty(_get_height, None, bind=('_rotation', '_size'))
    '''Rotated window height.

    :data:`height` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_center(self):
        return self.width / 2., self.height / 2.

    center = AliasProperty(_get_center, None, bind=('width', 'height'))
    '''Center of the rotated window.

    :data:`center` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_rotation(self):
        return self._rotation

    def _set_rotation(self, x):
        x = int(x % 360)
        if x == self._rotation:
            return
        if x not in (0, 90, 180, 270):
            raise ValueError('can rotate only 0, 90, 180, 270 degrees')
        self._rotation = x
        self.dispatch('on_resize', *self.size)
        self.dispatch('on_rotate', x)

    rotation = AliasProperty(_get_rotation, _set_rotation, bind=('_rotation', ))
    '''Get/set the window content rotation. Can be one of 0, 90, 180, 270
    degrees.
    '''

    def _get_system_size(self):
        return self._size

    system_size = AliasProperty(_get_system_size, None, bind=('_size', ))
    '''Real size of the window, without taking care of the rotation.
    '''

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

        super(WindowBase, self).__init__()

        # init privates
        self._system_keyboard = Keyboard(window=self)
        self._keyboards = {'system': self._system_keyboard}
        self._vkeyboard_cls = None

        self.children = []
        self.parent = self

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
        __import__('kivy.core.gl')

        # configure the window
        self.params = params
        self.create_window()

        # attach modules + listener event
        Modules.register_window(self)
        EventLoop.set_window(self)
        EventLoop.add_event_listener(self)

        # manage keyboard(s)
        self.configure_keyboards()

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

    def _update_childsize(self, instance, value):
        self.update_childsize([instance])

    def add_widget(self, widget):
        '''Add a widget on window'''
        widget.parent = self
        self.children.insert(0, widget)
        self.canvas.add(widget.canvas)
        self.update_childsize([widget])
        widget.bind(
            pos_hint=self._update_childsize,
            size_hint=self._update_childsize,
            size=self._update_childsize,
            pos=self._update_childsize)

    def remove_widget(self, widget):
        '''Remove a widget from window
        '''
        if not widget in self.children:
            return
        self.children.remove(widget)
        self.canvas.remove(widget.canvas)
        widget.parent = None
        widget.unbind(
            pos_hint=self._update_childsize,
            size_hint=self._update_childsize,
            size=self._update_childsize,
            pos=self._update_childsize)

    def clear(self):
        '''Clear the window with background color'''
        # XXX FIXME use late binding
        from kivy.graphics.opengl import glClearColor, glClear, \
            GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
        cc = self._clearcolor
        if cc is not None:
            glClearColor(*cc)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def set_title(self, title):
        '''Set the window title.

        .. versionadded:: 1.0.5
        '''
        pass

    def set_icon(self, filename):
        '''Set the icon of the window

        .. versionadded:: 1.0.5
        '''
        pass

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
        from math import radians

        w, h = self.system_size
        w2, h2 = w / 2., h / 2.
        r = radians(self.rotation)

        # prepare the viewport
        glViewport(0, 0, w, h)

        # do projection matrix
        projection_mat = Matrix()
        projection_mat.view_clip(0.0, w, 0.0, h, -1.0, 1.0, 0)
        self.render_context['projection_mat'] = projection_mat

        # do modelview matrix
        modelview_mat = Matrix().translate(w2, h2, 0)
        modelview_mat = modelview_mat.multiply(Matrix().rotate(r, 0, 0, 1))

        w, h = self.size
        w2, h2 = w / 2., h / 2.
        modelview_mat = modelview_mat.multiply(Matrix().translate(-w2, -h2, 0))
        self.render_context['modelview_mat'] = modelview_mat

        # redraw canvas
        self.canvas.ask_update()

        # and update childs
        self.update_childsize()

    def update_childsize(self, childs=None):
        width, height = self.size
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

    def screenshot(self, name='screenshot%(counter)04d.jpg'):
        '''Save the actual displayed image in a file
        '''
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

    def on_key_up(self, key, scancode=None, unicode=None, modifier=None):
        '''Event called when a key is up (same arguments as on_keyboard)'''
        pass

    def configure_keyboards(self):
        # Configure how to provide keyboards (virtual or not)

        # register system keyboard to listening keys from window
        sk = self._system_keyboard
        self.bind(
            on_key_down=sk._on_window_key_down,
            on_key_up=sk._on_window_key_up)

        # use the device's real keyboard
        self.allow_vkeyboard = False

        # one single vkeyboard shared between all widgets
        self.single_vkeyboard = True

        # the single vkeyboard is always sitting at the same position
        self.docked_vkeyboard = False

        # now read the configuration
        mode = Config.get('kivy', 'keyboard_mode')
        if mode not in ('', 'system', 'dock', 'multi'):
            Logger.critical('Window: unknown keyboard mode %r' % mode)

        # adapt mode according to the configuration
        if mode == 'system':
            self.allow_vkeyboard = False
            self.single_vkeyboard = True
            self.docked_vkeyboard = False
        elif mode == 'dock':
            self.allow_vkeyboard = True
            self.single_vkeyboard = True
            self.docked_vkeyboard = True
        elif mode == 'multi':
            self.allow_vkeyboard = True
            self.single_vkeyboard = False
            self.docked_vkeyboard = False

        Logger.info('Window: virtual keyboard %sallowed, %s, %s' %
                ('' if self.allow_vkeyboard else 'not ',
                'single mode' if self.single_vkeyboard else 'multiuser mode',
                'docked' if self.docked_vkeyboard else 'not docked'))

    def set_vkeyboard_class(self, cls):
        '''.. versionadded:: 1.0.8

        Set the VKeyboard class to use. If None set, it will use the
        :class:`kivy.uix.vkeyboard.VKeyboard`.
        '''
        self._vkeyboard_cls = cls

    def release_all_keyboards(self):
        '''.. versionadded:: 1.0.8

        This will ensure that no virtual keyboard / system keyboard are actually
        requested. All will be closed.
        '''
        for key in self._keyboards.keys()[:]:
            keyboard = self._keyboards[key]
            if keyboard:
                keyboard.release()

    def request_keyboard(self, callback, target):
        '''.. versionadded:: 1.0.4

        Internal method for widget, to request the keyboard. This method is
        not intented to be used by end-user, however, if you want to use the
        real-keyboard (not virtual keyboard), you don't want to share it with
        another widget.

        A widget can request the keyboard, indicating a callback to call
        when the keyboard will be released (or taken by another widget).

        :Parameters:
            `callback`: func
                Callback that will be called when the keyboard is closed. It can
                be because somebody else requested the keyboard, or if the user
                itself closed it.
            `target`: Widget
                Attach the keyboard to the specified target. Ensure you have a
                target attached if you're using the keyboard in a multi users
                mode.

        :Return:
            An instance of :class:`Keyboard`, containing the callback, target,
            and if configuration allowed it, a VKeyboard instance.

        .. versionchanged:: 1.0.8

            `target` have been added, and must be the widget source that request
            the keyboard. If set, the widget must have one method named
            `on_keyboard_text`, that will be called from the vkeyboard.

        '''

        # release any previous keyboard attached.
        self.release_keyboard(target)

        # if we can use virtual vkeyboard, activate it.
        if self.allow_vkeyboard:
            keyboard = None

            # late import
            global VKeyboard
            if VKeyboard is None and self._vkeyboard_cls is None:
                from kivy.uix.vkeyboard import VKeyboard
                self._vkeyboard_cls = VKeyboard

            # if the keyboard doesn't exist, create it.
            key = 'single' if self.single_vkeyboard else target
            if key not in self._keyboards:
                vkeyboard = self._vkeyboard_cls()
                keyboard = Keyboard(widget=vkeyboard, window=self)
                vkeyboard.bind(
                    on_key_down=keyboard._on_vkeyboard_key_down,
                    on_key_up=keyboard._on_vkeyboard_key_up)
                self._keyboards[key] = keyboard
            else:
                keyboard = self._keyboards[key]

            # configure vkeyboard
            keyboard.target = keyboard.widget.target = target
            keyboard.callback = keyboard.widget.callback = callback

            # add to the window
            self.add_widget(keyboard.widget)

            # only after add, do dock mode
            keyboard.widget.docked = self.docked_vkeyboard
            keyboard.widget.setup_mode()

            # return it.
            return keyboard

        else:
            # system keyboard, just register the callback.
            self._system_keyboard.callback = callback
            self._system_keyboard.target = target
            return self._system_keyboard

    def release_keyboard(self, target=None):
        '''.. versionadded:: 1.0.4

        Internal method for widget, to release the real-keyboard. Check
        :func:`request_keyboard` to understand how it works.
        '''
        if self.allow_vkeyboard:
            key = 'single' if self.single_vkeyboard else target
            if key not in self._keyboards:
                return
            keyboard = self._keyboards[key]
            callback = keyboard.callback
            if callback:
                keyboard.callback = None
                callback()
            keyboard.target = None
            self.remove_widget(keyboard.widget)
            if key != 'single' and key in self._keyboards:
                del self._keyboards[key]
        elif self._system_keyboard.callback:
            # this way will prevent possible recursion.
            callback = self._system_keyboard.callback
            self._system_keyboard.callback = None
            callback()
            return True


#: Instance of a :class:`WindowBase` implementation
Window = core_select_lib('window', (
    ('pygame', 'window_pygame', 'WindowPygame'),
), True)


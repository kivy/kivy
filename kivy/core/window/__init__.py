# pylint: disable=W0611
# coding: utf-8
'''
Window
======

Core class for creating the default Kivy window. Kivy supports only one window
per application: please don't try to create more than one.
'''

__all__ = ('Keyboard', 'WindowBase', 'Window')

from os.path import join, exists
from os import getcwd

from kivy.core import core_select_lib
from kivy.clock import Clock
from kivy.config import Config
from kivy.logger import Logger
from kivy.base import EventLoop, stopTouchApp
from kivy.modules import Modules
from kivy.event import EventDispatcher
from kivy.properties import ListProperty, ObjectProperty, AliasProperty, \
    NumericProperty, OptionProperty, StringProperty, BooleanProperty
from kivy.utils import platform, reify, deprecated
from kivy.context import get_current_context
from kivy.uix.behaviors import FocusBehavior
from kivy.setupconfig import USE_SDL2
from kivy.graphics.transformation import Matrix

# late import
VKeyboard = None
android = None
Animation = None


class Keyboard(EventDispatcher):
    '''Keyboard interface that is returned by
    :meth:`WindowBase.request_keyboard`. When you request a keyboard,
    you'll get an instance of this class. Whatever the keyboard input is
    (system or virtual keyboard), you'll receive events through this
    instance.

    :Events:
        `on_key_down`: keycode, text, modifiers
            Fired when a new key is pressed down
        `on_key_up`: keycode
            Fired when a key is released (up)

    Here is an example of how to request a Keyboard in accordance with the
    current configuration:

    .. include:: ../../examples/widgets/keyboardlistener.py
        :literal:

    '''

    # Keycodes mapping, between str <-> int. These keycodes are
    # currently taken from pygame.key. But when a new provider will be
    # used, it must do the translation to these keycodes too.
    keycodes = {
        # specials keys
        'backspace': 8, 'tab': 9, 'enter': 13, 'rshift': 303, 'shift': 304,
        'alt': 308, 'rctrl': 306, 'lctrl': 305,
        'super': 309, 'alt-gr': 307, 'compose': 311, 'pipe': 310,
        'capslock': 301, 'escape': 27, 'spacebar': 32, 'pageup': 280,
        'pagedown': 281, 'end': 279, 'home': 278, 'left': 276, 'up':
        273, 'right': 275, 'down': 274, 'insert': 277, 'delete': 127,
        'numlock': 300, 'print': 144, 'screenlock': 145, 'pause': 19,

        # a-z keys
        'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101, 'f': 102, 'g': 103,
        'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110,
        'o': 111, 'p': 112, 'q': 113, 'r': 114, 's': 115, 't': 116, 'u': 117,
        'v': 118, 'w': 119, 'x': 120, 'y': 121, 'z': 122,

        # 0-9 keys
        '0': 48, '1': 49, '2': 50, '3': 51, '4': 52,
        '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,

        # numpad
        'numpad0': 256, 'numpad1': 257, 'numpad2': 258, 'numpad3': 259,
        'numpad4': 260, 'numpad5': 261, 'numpad6': 262, 'numpad7': 263,
        'numpad8': 264, 'numpad9': 265, 'numpaddecimal': 266,
        'numpaddivide': 267, 'numpadmul': 268, 'numpadsubstract': 269,
        'numpadadd': 270, 'numpadenter': 271,

        # F1-15
        'f1': 282, 'f2': 283, 'f3': 284, 'f4': 285, 'f5': 286, 'f6': 287,
        'f7': 288, 'f8': 289, 'f9': 290, 'f10': 291, 'f11': 292, 'f12': 293,
        'f13': 294, 'f14': 295, 'f15': 296,

        # other keys
        '(': 40, ')': 41,
        '[': 91, ']': 93,
        '{': 123, '}': 125,
        ':': 58, ';': 59,
        '=': 61, '+': 43,
        '-': 45, '_': 95,
        '/': 47, '*': 42,
        '?': 47,
        '`': 96, '~': 126,
        '´': 180, '¦': 166,
        '\\': 92, '|': 124,
        '"': 34, "'": 39,
        ',': 44, '.': 46,
        '<': 60, '>': 62,
        '@': 64, '!': 33,
        '#': 35, '$': 36,
        '%': 37, '^': 94,
        '&': 38, '¬': 172,
        '¨': 168, '…': 8230,
        'ù': 249, 'à': 224,
        'é': 233, 'è': 232,
    }

    __events__ = ('on_key_down', 'on_key_up', 'on_textinput')

    def __init__(self, **kwargs):
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

    def on_textinput(self, text):
        pass

    def release(self):
        '''Call this method to release the current keyboard.
        This will ensure that the keyboard is no longer attached to your
        callback.'''
        if self.window:
            self.window.release_keyboard(self.target)

    def _on_window_textinput(self, instance, text):
        return self.dispatch('on_textinput', text)

    def _on_window_key_down(self, instance, keycode, scancode, text,
                            modifiers):
        keycode = (keycode, self.keycode_to_string(keycode))
        if text == '\x04':
            Window.trigger_keyboard_height()
            return
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

    def _on_vkeyboard_textinput(self, instance, text):
        return self.dispatch('on_textinput', text)

    def string_to_keycode(self, value):
        '''Convert a string to a keycode number according to the
        :attr:`Keyboard.keycodes`. If the value is not found in the
        keycodes, it will return -1.
        '''
        return Keyboard.keycodes.get(value, -1)

    def keycode_to_string(self, value):
        '''Convert a keycode number to a string according to the
        :attr:`Keyboard.keycodes`. If the value is not found in the
        keycodes, it will return ''.
        '''
        keycodes = list(Keyboard.keycodes.values())
        if value in keycodes:
            return list(Keyboard.keycodes.keys())[keycodes.index(value)]
        return ''


class WindowBase(EventDispatcher):
    '''WindowBase is an abstract window widget for any window implementation.

    :Parameters:
        `borderless`: str, one of ('0', '1')
            Set the window border state. Check the
            :mod:`~kivy.config` documentation for a
            more detailed explanation on the values.
        `fullscreen`: str, one of ('0', '1', 'auto', 'fake')
            Make the window fullscreen. Check the
            :mod:`~kivy.config` documentation for a
            more detailed explanation on the values.
        `width`: int
            Width of the window.
        `height`: int
            Height of the window.
        `minimum_width`: int
            Minimum width of the window (only works for sdl2 window provider).
        `minimum_height`: int
            Minimum height of the window (only works for sdl2 window provider).
        `allow_screensaver`: bool
            Allow the device to show a screen saver, or to go to sleep
            on mobile devices. Defaults to True. Only works for sdl2 window
            provider.

    :Events:
        `on_motion`: etype, motionevent
            Fired when a new :class:`~kivy.input.motionevent.MotionEvent` is
            dispatched
        `on_touch_down`:
            Fired when a new touch event is initiated.
        `on_touch_move`:
            Fired when an existing touch event changes location.
        `on_touch_up`:
            Fired when an existing touch event is terminated.
        `on_draw`:
            Fired when the :class:`Window` is being drawn.
        `on_flip`:
            Fired when the :class:`Window` GL surface is being flipped.
        `on_rotate`: rotation
            Fired when the :class:`Window` is being rotated.
        `on_close`:
            Fired when the :class:`Window` is closed.
        `on_request_close`:
            Fired when the event loop wants to close the window, or if the
            escape key is pressed and `exit_on_escape` is `True`. If a function
            bound to this event returns `True`, the window will not be closed.
            If the the event is triggered because of the keyboard escape key,
            the keyword argument `source` is dispatched along with a value of
            `keyboard` to the bound functions.

            .. versionadded:: 1.9.0

        `on_cursor_enter`:
            Fired when the cursor enters the window.

            .. versionadded:: 1.9.1

        `on_cursor_leave`:
            Fired when the cursor leaves the window.

            .. versionadded:: 1.9.1

        `on_minimize`:
            Fired when the window is minimized.

            .. versionadded:: 1.10.0

        `on_maximize`:
            Fired when the window is maximized.

            .. versionadded:: 1.10.0

        `on_restore`:
            Fired when the window is restored.

            .. versionadded:: 1.10.0

        `on_hide`:
            Fired when the window is hidden.

            .. versionadded:: 1.10.0

        `on_show`:
            Fired when when the window is shown.

            .. versionadded:: 1.10.0

        `on_keyboard`: key, scancode, codepoint, modifier
            Fired when the keyboard is used for input.

            .. versionchanged:: 1.3.0
                The *unicode* parameter has been deprecated in favor of
                codepoint, and will be removed completely in future versions.

        `on_key_down`: key, scancode, codepoint, modifier
            Fired when a key pressed.

            .. versionchanged:: 1.3.0
                The *unicode* parameter has been deprecated in favor of
                codepoint, and will be removed completely in future versions.

        `on_key_up`: key, scancode, codepoint
            Fired when a key is released.

            .. versionchanged:: 1.3.0
                The *unicode* parameter has be deprecated in favor of
                codepoint, and will be removed completely in future versions.

        `on_dropfile`: str
            Fired when a file is dropped on the application.

            .. note::
                This event doesn't work for apps with elevated permissions,
                because the OS API calls are filtered. Check issue
                `#4999 <https://github.com/kivy/kivy/issues/4999>`_ for
                pointers to workarounds.

        `on_memorywarning`:
            Fired when the platform have memory issue (iOS / Android mostly)
            You can listen to this one, and clean whatever you can.

            .. versionadded:: 1.9.0
    '''

    __instance = None
    __initialized = False
    _fake_fullscreen = False
    _density = 1

    # private properties
    _size = ListProperty([0, 0])
    _modifiers = ListProperty([])
    _rotation = NumericProperty(0)
    _clearcolor = ObjectProperty([0, 0, 0, 1])
    _focus = BooleanProperty(True)

    children = ListProperty([])
    '''List of the children of this window.

    :attr:`children` is a :class:`~kivy.properties.ListProperty` instance and
    defaults to an empty list.

    Use :meth:`add_widget` and :meth:`remove_widget` to manipulate the list of
    children. Don't manipulate the list directly unless you know what you are
    doing.
    '''

    parent = ObjectProperty(None, allownone=True)
    '''Parent of this window.

    :attr:`parent` is a :class:`~kivy.properties.ObjectProperty` instance and
    defaults to None. When created, the parent is set to the window itself.
    You must take care of it if you are doing a recursive check.
    '''

    icon = StringProperty()
    '''A path to the window icon.

    .. versionadded:: 1.1.2

    :attr:`icon` is a :class:`~kivy.properties.StringProperty`.
    '''

    def _get_modifiers(self):
        return self._modifiers

    modifiers = AliasProperty(_get_modifiers, None)
    '''List of keyboard modifiers currently active.

    .. versionadded:: 1.0.9

    :attr:`modifiers` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_size(self):
        r = self._rotation
        w, h = self._size
        if self._density != 1:
            w, h = self._win._get_gl_size()
        if self.softinput_mode == 'resize':
            h -= self.keyboard_height
        if r in (0, 180):
            return w, h
        return h, w

    def _set_size(self, size):
        if self._size != size:
            r = self._rotation
            if r in (0, 180):
                self._size = size
            else:
                self._size = size[1], size[0]

            self.dispatch('on_resize', *size)
            return True
        else:
            return False

    minimum_width = NumericProperty(0)
    '''The minimum width to restrict the window to.

    .. versionadded:: 1.9.1

    :attr:`minimum_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_height = NumericProperty(0)
    '''The minimum height to restrict the window to.

    .. versionadded:: 1.9.1

    :attr:`minimum_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    allow_screensaver = BooleanProperty(True)
    '''Whether the screen saver is enabled, or on mobile devices whether the
    device is allowed to go to sleep while the app is open.

    .. versionadded:: 1.10.0

    :attr:`allow_screensaver` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    size = AliasProperty(_get_size, _set_size, bind=('_size', ))
    '''Get the rotated size of the window. If :attr:`rotation` is set, then the
    size will change to reflect the rotation.

    .. versionadded:: 1.0.9

    :attr:`size` is an :class:`~kivy.properties.AliasProperty`.
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
    '''Color used to clear the window.

    ::

        from kivy.core.window import Window

        # red background color
        Window.clearcolor = (1, 0, 0, 1)

        # don't clear background at all
        Window.clearcolor = None

    .. versionchanged:: 1.7.2
        The clearcolor default value is now: (0, 0, 0, 1).

    .. versionadded:: 1.0.9

    :attr:`clearcolor` is an :class:`~kivy.properties.AliasProperty` and
    defaults to (0, 0, 0, 1).
    '''

    # make some property read-only
    def _get_width(self):
        _size = self._size
        if self._density != 1:
            _size = self._win._get_gl_size()
        r = self._rotation
        if r == 0 or r == 180:
            return _size[0]
        return _size[1]

    width = AliasProperty(_get_width, None, bind=('_rotation', '_size'))
    '''Rotated window width.

    :attr:`width` is a read-only :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_height(self):
        '''Rotated window height'''
        r = self._rotation
        _size = self._size
        if self._density != 1:
            _size = self._win._get_gl_size()
        kb = self.keyboard_height if self.softinput_mode == 'resize' else 0
        if r == 0 or r == 180:
            return _size[1] - kb
        return _size[0] - kb

    height = AliasProperty(_get_height, None, bind=('_rotation', '_size'))
    '''Rotated window height.

    :attr:`height` is a read-only :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_center(self):
        return self.width / 2., self.height / 2.

    center = AliasProperty(_get_center, None, bind=('width', 'height'))
    '''Center of the rotated window.

    .. versionadded:: 1.0.9

    :attr:`center` is an :class:`~kivy.properties.AliasProperty`.
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
        if not self.initialized:
            return
        self.dispatch('on_resize', *self.size)
        self.dispatch('on_rotate', x)

    rotation = AliasProperty(_get_rotation, _set_rotation,
                             bind=('_rotation', ))
    '''Get/set the window content rotation. Can be one of 0, 90, 180, 270
    degrees.

    .. versionadded:: 1.0.9

    :attr:`rotation` is an :class:`~kivy.properties.AliasProperty`.
    '''

    softinput_mode = OptionProperty('', options=(
        '', 'below_target', 'pan', 'scale', 'resize'))
    '''This specifies the behavior of window contents on display of the soft
    keyboard on mobile platforms. It can be one of '', 'pan', 'scale',
    'resize' or 'below_target'. Their effects are listed below.

    +----------------+-------------------------------------------------------+
    | Value          | Effect                                                |
    +================+=======================================================+
    | ''             | The main window is left as is, allowing you to use    |
    |                | the :attr:`keyboard_height` to manage the window      |
    |                | contents manually.                                    |
    +----------------+-------------------------------------------------------+
    | 'pan'          | The main window pans, moving the bottom part of the   |
    |                | window to be always on top of the keyboard.           |
    +----------------+-------------------------------------------------------+
    | 'resize'       | The window is resized and the contents scaled to fit  |
    |                | the remaining space.                                  |
    +----------------+-------------------------------------------------------+
    | 'below_target' | The window pans so that the current target TextInput  |
    |                | widget requesting the keyboard is presented just above|
    |                | the soft keyboard.                                    |
    +----------------+-------------------------------------------------------+

    :attr:`softinput_mode` is an :class:`~kivy.properties.OptionProperty` and
    defaults to `None`.

    .. note:: The `resize` option does not currently work with SDL2 on Android.

    .. versionadded:: 1.9.0

    .. versionchanged:: 1.9.1
        The 'below_target' option was added.
    '''

    _keyboard_changed = BooleanProperty(False)
    _kheight = NumericProperty(0)

    def _animate_content(self):
        '''Animate content to IME height.
        '''
        kargs = self.keyboard_anim_args
        global Animation
        if not Animation:
            from kivy.animation import Animation
        Animation.cancel_all(self)
        Animation(
            _kheight=self.keyboard_height + self.keyboard_padding,
            d=kargs['d'], t=kargs['t']).start(self)

    def _upd_kbd_height(self, *kargs):
        self._keyboard_changed = not self._keyboard_changed
        self._animate_content()

    def _get_ios_kheight(self):
        import ios
        return ios.get_kheight()

    def _get_android_kheight(self):
        if USE_SDL2:  # Placeholder until the SDL2 bootstrap supports this
            return 0
        global android
        if not android:
            import android
        return android.get_keyboard_height()

    def _get_kheight(self):
        if platform == 'android':
            return self._get_android_kheight()
        if platform == 'ios':
            return self._get_ios_kheight()
        return 0

    keyboard_height = AliasProperty(_get_kheight, None,
                                    bind=('_keyboard_changed',), cached=True)
    '''Returns the height of the softkeyboard/IME on mobile platforms.
    Will return 0 if not on mobile platform or if IME is not active.

    .. note:: This property returns 0 with SDL2 on Android, but setting
              Window.softinput_mode does works.

    .. versionadded:: 1.9.0

    :attr:`keyboard_height` is a read-only
    :class:`~kivy.properties.AliasProperty` and defaults to 0.
    '''

    keyboard_anim_args = {'t': 'in_out_quart', 'd': .5}
    '''The attributes for animating softkeyboard/IME.
    `t` = `transition`, `d` = `duration`. Will have no effect on desktops.

    .. versionadded:: 1.10.0

    :attr:`keyboard_anim_args` is a dict with values
    't': 'in_out_quart', 'd': `.5`.
    '''

    keyboard_padding = NumericProperty(0)
    '''The padding to have between the softkeyboard/IME & target
    or bottom of window. Will have no effect on desktops.

    .. versionadded:: 1.10.0

    :attr:`keyboard_padding` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.
    '''

    def _set_system_size(self, size):
        self._size = size

    def _get_system_size(self):
        if self.softinput_mode == 'resize':
            return self._size[0], self._size[1] - self.keyboard_height
        return self._size

    system_size = AliasProperty(
        _get_system_size,
        _set_system_size,
        bind=('_size', ))
    '''Real size of the window ignoring rotation.

    .. versionadded:: 1.0.9

    :attr:`system_size` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_effective_size(self):
        '''On density=1 and non-ios displays, return system_size, else
        return scaled / rotated size.

        Used by MouseMotionEvent.update_graphics() and WindowBase.on_motion().
        '''
        w, h = self.system_size
        if platform == 'ios' or self._density != 1:
            w, h = self.size

        return w, h

    borderless = BooleanProperty(False)
    '''When set to True, this property removes the window border/decoration.
    Check the :mod:`~kivy.config` documentation for a more detailed
    explanation on the values.

    .. versionadded:: 1.9.0

    :attr:`borderless` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    fullscreen = OptionProperty(False, options=(True, False, 'auto', 'fake'))
    '''This property sets the fullscreen mode of the window. Available options
    are: True, False, 'auto' and 'fake'. Check the :mod:`~kivy.config`
    documentation for more detailed explanations on these values.

    fullscreen is an :class:`~kivy.properties.OptionProperty` and defaults to
    `False`.

    .. versionadded:: 1.2.0

    .. note::
        The 'fake' option has been deprecated, use the :attr:`borderless`
        property instead.
    '''

    mouse_pos = ObjectProperty([0, 0])
    '''2d position of the mouse within the window.

    .. versionadded:: 1.2.0

    :attr:`mouse_pos` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to [0, 0].
    '''

    show_cursor = BooleanProperty(True)
    '''Set whether or not the cursor is shown on the window.

    .. versionadded:: 1.9.1

    :attr:`show_cursor` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    def _get_focus(self):
        return self._focus

    focus = AliasProperty(_get_focus, None, bind=('_focus',))
    '''Check whether or not the window currently has focus.

    .. versionadded:: 1.9.1

    :attr:`focus` is a read-only :class:`~kivy.properties.AliasProperty` and
    defaults to True.
    '''

    def _set_cursor_state(self, value):
        pass

    def _get_window_pos(self):
        pass

    def _set_window_pos(self, x, y):
        pass

    def _get_left(self):
        if not self.initialized:
            return self._left
        return self._get_window_pos()[0]

    def _set_left(self, value):
        pos = self._get_window_pos()
        self._set_window_pos(value, pos[1])

    def _get_top(self):
        if not self.initialized:
            return self._top
        return self._get_window_pos()[1]

    def _set_top(self, value):
        pos = self._get_window_pos()
        self._set_window_pos(pos[0], value)

    top = AliasProperty(_get_top, _set_top)
    '''Top position of the window.

    .. note:: It's an SDL2 property with `[0, 0]` in the top-left corner.

    .. versionchanged:: 1.10.0
        :attr:`top` is now an :class:`~kivy.properties.AliasProperty`

    .. versionadded:: 1.9.1

    :attr:`top` is an :class:`~kivy.properties.AliasProperty` and defaults to
    position set in :class:`~kivy.config.Config`.
    '''

    left = AliasProperty(_get_left, _set_left)
    '''Left position of the window.

    .. note:: It's an SDL2 property with `[0, 0]` in the top-left corner.

    .. versionchanged:: 1.10.0
        :attr:`left` is now an :class:`~kivy.properties.AliasProperty`

    .. versionadded:: 1.9.1

    :attr:`left` is an :class:`~kivy.properties.AliasProperty` and defaults to
    position set in :class:`~kivy.config.Config`.
    '''

    @property
    def __self__(self):
        return self

    position = OptionProperty('auto', options=['auto', 'custom'])
    render_context = ObjectProperty(None)
    canvas = ObjectProperty(None)
    title = StringProperty('Kivy')

    trigger_create_window = None

    __events__ = (
        'on_draw', 'on_flip', 'on_rotate', 'on_resize', 'on_close',
        'on_minimize', 'on_maximize', 'on_restore', 'on_hide', 'on_show',
        'on_motion', 'on_touch_down', 'on_touch_move', 'on_touch_up',
        'on_mouse_down', 'on_mouse_move', 'on_mouse_up', 'on_keyboard',
        'on_key_down', 'on_key_up', 'on_textinput', 'on_dropfile',
        'on_request_close', 'on_cursor_enter', 'on_cursor_leave',
        'on_joy_axis', 'on_joy_hat', 'on_joy_ball',
        'on_joy_button_down', 'on_joy_button_up', 'on_memorywarning')

    def __new__(cls, **kwargs):
        if cls.__instance is None:
            cls.__instance = EventDispatcher.__new__(cls)
        return cls.__instance

    def __init__(self, **kwargs):

        force = kwargs.pop('force', False)

        # don't init window 2 times,
        # except if force is specified
        if WindowBase.__instance is not None and not force:
            return

        self.initialized = False
        self._is_desktop = Config.getboolean('kivy', 'desktop')

        # create a trigger for update/create the window when one of window
        # property changes
        self.trigger_create_window = Clock.create_trigger(
            self.create_window, -1)

        # Create a trigger for updating the keyboard height
        self.trigger_keyboard_height = Clock.create_trigger(
            self._upd_kbd_height, .5)
        self.bind(_kheight=lambda *args: self.update_viewport())

        # set the default window parameter according to the configuration
        if 'borderless' not in kwargs:
            kwargs['borderless'] = Config.getboolean('graphics', 'borderless')
        if 'fullscreen' not in kwargs:
            fullscreen = Config.get('graphics', 'fullscreen')
            if fullscreen not in ('auto', 'fake'):
                fullscreen = fullscreen.lower() in ('true', '1', 'yes')
            kwargs['fullscreen'] = fullscreen
        if 'width' not in kwargs:
            kwargs['width'] = Config.getint('graphics', 'width')
        if 'height' not in kwargs:
            kwargs['height'] = Config.getint('graphics', 'height')
        if 'minimum_width' not in kwargs:
            kwargs['minimum_width'] = Config.getint('graphics',
                                                    'minimum_width')
        if 'minimum_height' not in kwargs:
            kwargs['minimum_height'] = Config.getint('graphics',
                                                     'minimum_height')
        if 'allow_screensaver' not in kwargs:
            kwargs['allow_screensaver'] = Config.getboolean(
                'graphics', 'allow_screensaver')
        if 'rotation' not in kwargs:
            kwargs['rotation'] = Config.getint('graphics', 'rotation')
        if 'position' not in kwargs:
            kwargs['position'] = Config.getdefault('graphics', 'position',
                                                   'auto')
        if 'top' in kwargs:
            kwargs['position'] = 'custom'
            self._top = kwargs['top']
        else:
            self._top = Config.getint('graphics', 'top')
        if 'left' in kwargs:
            kwargs['position'] = 'custom'
            self._left = kwargs['left']
        else:
            self._left = Config.getint('graphics', 'left')
        kwargs['_size'] = (kwargs.pop('width'), kwargs.pop('height'))
        if 'show_cursor' not in kwargs:
            kwargs['show_cursor'] = Config.getboolean('graphics',
                                                      'show_cursor')

        super(WindowBase, self).__init__(**kwargs)

        # bind all the properties that need to recreate the window
        self._bind_create_window()
        self.bind(size=self.trigger_keyboard_height,
                  rotation=self.trigger_keyboard_height)

        self.bind(softinput_mode=lambda *dt: self.update_viewport(),
                  keyboard_height=lambda *dt: self.update_viewport())

        self.bind(show_cursor=lambda *dt: self._set_cursor_state(dt[1]))

        # init privates
        self._system_keyboard = Keyboard(window=self)
        self._keyboards = {'system': self._system_keyboard}
        self._vkeyboard_cls = None

        self.children = []
        self.parent = self

        # before creating the window
        import kivy.core.gl  # NOQA

        # configure the window
        self.create_window()

        # attach modules + listener event
        EventLoop.set_window(self)
        Modules.register_window(self)
        EventLoop.add_event_listener(self)

        # manage keyboard(s)
        self.configure_keyboards()

        # assign the default context of the widget creation
        if not hasattr(self, '_context'):
            self._context = get_current_context()

        # mark as initialized
        self.initialized = True

    def _bind_create_window(self):
        for prop in (
                'fullscreen', 'borderless', 'position', 'top',
                'left', '_size', 'system_size'):
            self.bind(**{prop: self.trigger_create_window})

    def _unbind_create_window(self):
        for prop in (
                'fullscreen', 'borderless', 'position', 'top',
                'left', '_size', 'system_size'):
            self.unbind(**{prop: self.trigger_create_window})

    @deprecated
    def toggle_fullscreen(self):
        '''Toggle between fullscreen and windowed mode.

        .. deprecated:: 1.9.0
            Use :attr:`fullscreen` instead.
        '''
        pass

    def maximize(self):
        '''Maximizes the window. This method should be used on desktop
        platforms only.

        .. versionadded:: 1.9.0

        .. note::
            This feature requires the SDL2 window provider and is currently
            only supported on desktop platforms.
        '''
        Logger.warning('Window: maximize() is not implemented in the current '
                        'window provider.')

    def minimize(self):
        '''Minimizes the window. This method should be used on desktop
        platforms only.

        .. versionadded:: 1.9.0

        .. note::
            This feature requires the SDL2 window provider and is currently
            only supported on desktop platforms.
        '''
        Logger.warning('Window: minimize() is not implemented in the current '
                        'window provider.')

    def restore(self):
        '''Restores the size and position of a maximized or minimized window.
        This method should be used on desktop platforms only.

        .. versionadded:: 1.9.0

        .. note::
            This feature requires the SDL2 window provider and is currently
            only supported on desktop platforms.
        '''
        Logger.warning('Window: restore() is not implemented in the current '
                        'window provider.')

    def hide(self):
        '''Hides the window. This method should be used on desktop
        platforms only.

        .. versionadded:: 1.9.0

        .. note::
            This feature requires the SDL2 window provider and is currently
            only supported on desktop platforms.
        '''
        Logger.warning('Window: hide() is not implemented in the current '
                        'window provider.')

    def show(self):
        '''Shows the window. This method should be used on desktop
        platforms only.

        .. versionadded:: 1.9.0

        .. note::
            This feature requires the SDL2 window provider and is currently
            only supported on desktop platforms.
        '''
        Logger.warning('Window: show() is not implemented in the current '
                        'window provider.')

    def raise_window(self):
        '''Raise the window. This method should be used on desktop
        platforms only.

        .. versionadded:: 1.9.1

        .. note::
            This feature requires the SDL2 window provider and is currently
            only supported on desktop platforms.
        '''
        Logger.warning('Window: raise_window is not implemented in the current'
                       ' window provider.')

    def close(self):
        '''Close the window'''
        pass

    def create_window(self, *largs):
        '''Will create the main window and configure it.

        .. warning::
            This method is called automatically at runtime. If you call it, it
            will recreate a RenderContext and Canvas. This means you'll have a
            new graphics tree, and the old one will be unusable.

            This method exist to permit the creation of a new OpenGL context
            AFTER closing the first one. (Like using runTouchApp() and
            stopTouchApp()).

            This method has only been tested in a unittest environment and
            is not suitable for Applications.

            Again, don't use this method unless you know exactly what you are
            doing!
        '''
        # just to be sure, if the trigger is set, and if this method is
        # manually called, unset the trigger
        self.trigger_create_window.cancel()

        # ensure the window creation will not be called twice
        if platform in ('android', 'ios'):
            self._unbind_create_window()

        if not self.initialized:
            from kivy.core.gl import init_gl
            init_gl()

            # create the render context and canvas, only the first time.
            from kivy.graphics import RenderContext, Canvas
            self.render_context = RenderContext()
            self.canvas = Canvas()
            self.render_context.add(self.canvas)

        else:
            # if we get initialized more than once, then reload opengl state
            # after the second time.
            # XXX check how it's working on embed platform.
            if platform == 'linux' or Window.__class__.__name__ == 'WindowSDL':
                # on linux, it's safe for just sending a resize.
                self.dispatch('on_resize', *self.system_size)

            else:
                # on other platform, window are recreated, we need to reload.
                from kivy.graphics.context import get_context
                get_context().reload()
                Clock.schedule_once(lambda x: self.canvas.ask_update(), 0)
                self.dispatch('on_resize', *self.system_size)

        # ensure the gl viewport is correct
        self.update_viewport()

    def on_flip(self):
        '''Flip between buffers (event)'''
        self.flip()

    def flip(self):
        '''Flip between buffers'''
        pass

    def _update_childsize(self, instance, value):
        self.update_childsize([instance])

    def add_widget(self, widget, canvas=None):
        '''Add a widget to a window'''
        widget.parent = self
        self.children.insert(0, widget)
        canvas = self.canvas.before if canvas == 'before' else \
            self.canvas.after if canvas == 'after' else self.canvas
        canvas.add(widget.canvas)
        self.update_childsize([widget])
        widget.bind(
            pos_hint=self._update_childsize,
            size_hint=self._update_childsize,
            size_hint_max=self._update_childsize,
            size_hint_min=self._update_childsize,
            size=self._update_childsize,
            pos=self._update_childsize)

    def remove_widget(self, widget):
        '''Remove a widget from a window
        '''
        if widget not in self.children:
            return
        self.children.remove(widget)
        if widget.canvas in self.canvas.children:
            self.canvas.remove(widget.canvas)
        elif widget.canvas in self.canvas.after.children:
            self.canvas.after.remove(widget.canvas)
        elif widget.canvas in self.canvas.before.children:
            self.canvas.before.remove(widget.canvas)
        widget.parent = None
        widget.unbind(
            pos_hint=self._update_childsize,
            size_hint=self._update_childsize,
            size_hint_max=self._update_childsize,
            size_hint_min=self._update_childsize,
            size=self._update_childsize,
            pos=self._update_childsize)

    def clear(self):
        '''Clear the window with the background color'''
        # XXX FIXME use late binding
        from kivy.graphics.opengl import glClearColor, glClear, \
            GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_STENCIL_BUFFER_BIT
        cc = self._clearcolor
        if cc is not None:
            glClearColor(*cc)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT |
                    GL_STENCIL_BUFFER_BIT)

    def set_title(self, title):
        '''Set the window title.

        .. versionadded:: 1.0.5
        '''
        self.title = title

    def set_icon(self, filename):
        '''Set the icon of the window.

        .. versionadded:: 1.0.5
        '''
        self.icon = filename

    def to_widget(self, x, y, initial=True, relative=False):
        return (x, y)

    def to_window(self, x, y, initial=True, relative=False):
        return (x, y)

    def _apply_transform(self, m):
        return m

    def get_window_matrix(self, x=0, y=0):
        m = Matrix()
        m.translate(x, y, 0)
        return m

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
                The Motion Event currently dispatched.
        '''
        if me.is_touch:
            w, h = self._get_effective_size()
            me.scale_for_screen(w, h, rotation=self._rotation,
                                smode=self.softinput_mode,
                                kheight=self.keyboard_height)
            if etype == 'begin':
                self.dispatch('on_touch_down', me)
            elif etype == 'update':
                self.dispatch('on_touch_move', me)
            elif etype == 'end':
                self.dispatch('on_touch_up', me)
                FocusBehavior._handle_post_on_touch_up(me)

    def on_touch_down(self, touch):
        '''Event called when a touch down event is initiated.

        .. versionchanged:: 1.9.0
            The touch `pos` is now transformed to window coordinates before
            this method is called. Before, the touch `pos` coordinate would be
            `(0, 0)` when this method was called.
        '''
        for w in self.children[:]:
            if w.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Event called when a touch event moves (changes location).

        .. versionchanged:: 1.9.0
            The touch `pos` is now transformed to window coordinates before
            this method is called. Before, the touch `pos` coordinate would be
            `(0, 0)` when this method was called.
        '''
        for w in self.children[:]:
            if w.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Event called when a touch event is released (terminated).

        .. versionchanged:: 1.9.0
            The touch `pos` is now transformed to window coordinates before
            this method is called. Before, the touch `pos` coordinate would be
            `(0, 0)` when this method was called.
        '''
        for w in self.children[:]:
            if w.dispatch('on_touch_up', touch):
                return True

    def on_resize(self, width, height):
        '''Event called when the window is resized.'''
        self.update_viewport()

    def update_viewport(self):
        from kivy.graphics.opengl import glViewport
        from kivy.graphics.transformation import Matrix
        from math import radians

        w, h = self.system_size
        if self._density != 1:
            w, h = self.size

        smode = self.softinput_mode
        target = self._system_keyboard.target
        targettop = max(0, target.to_window(0, target.y)[1]) if target else 0
        kheight = self._kheight

        w2, h2 = w / 2., h / 2.
        r = radians(self.rotation)

        x, y = 0, 0
        _h = h
        if smode == 'pan':
            y = kheight
        elif smode == 'below_target':
            y = 0 if kheight < targettop else (kheight - targettop)
        if smode == 'scale':
            _h -= kheight

        # prepare the viewport
        glViewport(x, y, w, _h)

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
            shw_min, shh_min = w.size_hint_min
            shw_max, shh_max = w.size_hint_max

            if shw is not None and shh is not None:
                c_w = shw * width
                c_h = shh * height

                if shw_min is not None and c_w < shw_min:
                    c_w = shw_min
                elif shw_max is not None and c_w > shw_max:
                    c_w = shw_max

                if shh_min is not None and c_h < shh_min:
                    c_h = shh_min
                elif shh_max is not None and c_h > shh_max:
                    c_h = shh_max
                w.size = c_w, c_h
            elif shw is not None:
                c_w = shw * width

                if shw_min is not None and c_w < shw_min:
                    c_w = shw_min
                elif shw_max is not None and c_w > shw_max:
                    c_w = shw_max
                w.width = c_w
            elif shh is not None:
                c_h = shh * height

                if shh_min is not None and c_h < shh_min:
                    c_h = shh_min
                elif shh_max is not None and c_h > shh_max:
                    c_h = shh_max
                w.height = c_h

            for key, value in w.pos_hint.items():
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

    def screenshot(self, name='screenshot{:04d}.png'):
        '''Save the actual displayed image in a file
        '''
        i = 0
        path = None
        if name != 'screenshot{:04d}.png':
            _ext = name.split('.')[-1]
            name = ''.join((name[:-(len(_ext) + 1)], '{:04d}.', _ext))
        while True:
            i += 1
            path = join(getcwd(), name.format(i))
            if not exists(path):
                break
        return path

    def on_rotate(self, rotation):
        '''Event called when the screen has been rotated.
        '''
        pass

    def on_close(self, *largs):
        '''Event called when the window is closed'''
        Modules.unregister_window(self)
        EventLoop.remove_event_listener(self)

    def on_minimize(self, *largs):
        '''Event called when the window is minimized.

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_maximize(self, *largs):
        '''Event called when the window is maximized.

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_restore(self, *largs):
        '''Event called when the window is restored.

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_hide(self, *largs):
        '''Event called when the window is hidden.

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_show(self, *largs):
        '''Event called when the window is shown.

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_request_close(self, *largs, **kwargs):
        '''Event called before we close the window. If a bound function returns
        `True`, the window will not be closed. If the the event is triggered
        because of the keyboard escape key, the keyword argument `source` is
        dispatched along with a value of `keyboard` to the bound functions.

        .. warning::
            When the bound function returns True the window will not be closed,
            so use with care because the user would not be able to close the
            program, even if the red X is clicked.
        '''
        pass

    def on_cursor_enter(self, *largs):
        '''Event called when the cursor enters the window.

        .. versionadded:: 1.9.1

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_cursor_leave(self, *largs):
        '''Event called when the cursor leaves the window.

        .. versionadded:: 1.9.1

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def on_mouse_down(self, x, y, button, modifiers):
        '''Event called when the mouse is used (pressed/released)'''
        pass

    def on_mouse_move(self, x, y, modifiers):
        '''Event called when the mouse is moved with buttons pressed'''
        pass

    def on_mouse_up(self, x, y, button, modifiers):
        '''Event called when the mouse is moved with buttons pressed'''
        pass

    def on_joy_axis(self, stickid, axisid, value):
        '''Event called when a joystick has a stick or other axis moved

        .. versionadded:: 1.9.0'''
        pass

    def on_joy_hat(self, stickid, hatid, value):
        '''Event called when a joystick has a hat/dpad moved

        .. versionadded:: 1.9.0'''
        pass

    def on_joy_ball(self, stickid, ballid, value):
        '''Event called when a joystick has a ball moved

        .. versionadded:: 1.9.0'''
        pass

    def on_joy_button_down(self, stickid, buttonid):
        '''Event called when a joystick has a button pressed

        .. versionadded:: 1.9.0'''
        pass

    def on_joy_button_up(self, stickid, buttonid):
        '''Event called when a joystick has a button released

        .. versionadded:: 1.9.0'''
        pass

    def on_keyboard(self, key, scancode=None, codepoint=None,
                    modifier=None, **kwargs):
        '''Event called when keyboard is used.

        .. warning::
            Some providers may omit `scancode`, `codepoint` and/or `modifier`.
        '''
        if 'unicode' in kwargs:
            Logger.warning("The use of the unicode parameter is deprecated, "
                           "and will be removed in future versions. Use "
                           "codepoint instead, which has identical "
                           "semantics.")

        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = platform == 'darwin'
        if WindowBase.on_keyboard.exit_on_escape:
            if key == 27 or all([is_osx, key in [113, 119], modifier == 1024]):
                if not self.dispatch('on_request_close', source='keyboard'):
                    stopTouchApp()
                    self.close()
                    return True

    if Config:
        on_keyboard.exit_on_escape = Config.getboolean(
                                        'kivy', 'exit_on_escape')

        def __exit(section, name, value):
            WindowBase.__dict__['on_keyboard'].exit_on_escape = \
                Config.getboolean('kivy', 'exit_on_escape')

        Config.add_callback(__exit, 'kivy', 'exit_on_escape')

    def on_key_down(self, key, scancode=None, codepoint=None,
                    modifier=None, **kwargs):
        '''Event called when a key is down (same arguments as on_keyboard)'''
        if 'unicode' in kwargs:
            Logger.warning("The use of the unicode parameter is deprecated, "
                           "and will be removed in future versions. Use "
                           "codepoint instead, which has identical "
                           "semantics.")

    def on_key_up(self, key, scancode=None, codepoint=None,
                  modifier=None, **kwargs):
        '''Event called when a key is released (same arguments as on_keyboard)
        '''
        if 'unicode' in kwargs:
            Logger.warning("The use of the unicode parameter is deprecated, "
                           "and will be removed in future versions. Use "
                           "codepoint instead, which has identical "
                           "semantics.")

    def on_textinput(self, text):
        '''Event called when text: i.e. alpha numeric non control keys or set
        of keys is entered. As it is not guaranteed whether we get one
        character or multiple ones, this event supports handling multiple
        characters.

        .. versionadded:: 1.9.0
        '''
        pass

    def on_dropfile(self, filename):
        '''Event called when a file is dropped on the application.

        .. warning::

            This event currently works with sdl2 window provider, on pygame
            window provider and OS X with a patched version of pygame.
            This event is left in place for further evolution
            (ios, android etc.)

        .. versionadded:: 1.2.0
        '''
        pass

    def on_memorywarning(self):
        '''Event called when the platform have memory issue.
        Your goal is to clear the cache in your app as much as you can,
        release unused widget, etc.

        Currently, this event is fired only from SDL2 provider, for
        iOS and Android.

        .. versionadded:: 1.9.0
        '''
        pass

    @reify
    def dpi(self):
        '''Return the DPI of the screen. If the implementation doesn't support
        any DPI lookup, it will just return 96.

        .. warning::

            This value is not cross-platform. Use
            :attr:`kivy.base.EventLoop.dpi` instead.
        '''
        return 96.

    def configure_keyboards(self):
        # Configure how to provide keyboards (virtual or not)

        # register system keyboard to listening keys from window
        sk = self._system_keyboard
        self.bind(
            on_key_down=sk._on_window_key_down,
            on_key_up=sk._on_window_key_up,
            on_textinput=sk._on_window_textinput)

        # use the device's real keyboard
        self.use_syskeyboard = True

        # use the device's real keyboard
        self.allow_vkeyboard = False

        # one single vkeyboard shared between all widgets
        self.single_vkeyboard = True

        # the single vkeyboard is always sitting at the same position
        self.docked_vkeyboard = False

        # now read the configuration
        mode = Config.get('kivy', 'keyboard_mode')
        if mode not in ('', 'system', 'dock', 'multi', 'systemanddock',
                        'systemandmulti'):
            Logger.critical('Window: unknown keyboard mode %r' % mode)

        # adapt mode according to the configuration
        if mode == 'system':
            self.use_syskeyboard = True
            self.allow_vkeyboard = False
            self.single_vkeyboard = True
            self.docked_vkeyboard = False
        elif mode == 'dock':
            self.use_syskeyboard = False
            self.allow_vkeyboard = True
            self.single_vkeyboard = True
            self.docked_vkeyboard = True
        elif mode == 'multi':
            self.use_syskeyboard = False
            self.allow_vkeyboard = True
            self.single_vkeyboard = False
            self.docked_vkeyboard = False
        elif mode == 'systemanddock':
            self.use_syskeyboard = True
            self.allow_vkeyboard = True
            self.single_vkeyboard = True
            self.docked_vkeyboard = True
        elif mode == 'systemandmulti':
            self.use_syskeyboard = True
            self.allow_vkeyboard = True
            self.single_vkeyboard = False
            self.docked_vkeyboard = False

        Logger.info(
            'Window: virtual keyboard %sallowed, %s, %s' % (
                '' if self.allow_vkeyboard else 'not ',
                'single mode' if self.single_vkeyboard else 'multiuser mode',
                'docked' if self.docked_vkeyboard else 'not docked'))

    def set_vkeyboard_class(self, cls):
        '''.. versionadded:: 1.0.8

        Set the VKeyboard class to use. If set to `None`, it will use the
        :class:`kivy.uix.vkeyboard.VKeyboard`.
        '''
        self._vkeyboard_cls = cls

    def release_all_keyboards(self):
        '''.. versionadded:: 1.0.8

        This will ensure that no virtual keyboard / system keyboard is
        requested. All instances will be closed.
        '''
        for key in list(self._keyboards.keys())[:]:
            keyboard = self._keyboards[key]
            if keyboard:
                keyboard.release()

    def request_keyboard(self, callback, target, input_type='text'):
        '''.. versionadded:: 1.0.4

        Internal widget method to request the keyboard. This method is rarely
        required by the end-user as it is handled automatically by the
        :class:`~kivy.uix.textinput.TextInput`. We expose it in case you want
        to handle the keyboard manually for unique input scenarios.

        A widget can request the keyboard, indicating a callback to call
        when the keyboard is released (or taken by another widget).

        :Parameters:
            `callback`: func
                Callback that will be called when the keyboard is
                closed. This can be because somebody else requested the
                keyboard or the user closed it.
            `target`: Widget
                Attach the keyboard to the specified `target`. This should be
                the widget that requested the keyboard. Ensure you have a
                different target attached to each keyboard if you're working in
                a multi user mode.

                .. versionadded:: 1.0.8

            `input_type`: string
                Choose the type of soft keyboard to request. Can be one of
                'text', 'number', 'url', 'mail', 'datetime', 'tel', 'address'.

                .. note::

                    `input_type` is currently only honored on mobile devices.

                .. versionadded:: 1.8.0

        :Return:
            An instance of :class:`Keyboard` containing the callback, target,
            and if the configuration allows it, a
            :class:`~kivy.uix.vkeyboard.VKeyboard` instance attached as a
            *.widget* property.

        .. note::

            The behavior of this function is heavily influenced by the current
            `keyboard_mode`. Please see the Config's
            :ref:`configuration tokens <configuration-tokens>` section for
            more information.

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
                    on_key_up=keyboard._on_vkeyboard_key_up,
                    on_textinput=keyboard._on_vkeyboard_textinput)
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

        else:
            # system keyboard, just register the callback.
            keyboard = self._system_keyboard
            keyboard.callback = callback
            keyboard.target = target

        # use system (hardware) keyboard according to flag
        if self.allow_vkeyboard and self.use_syskeyboard:
            self.unbind(
                on_key_down=keyboard._on_window_key_down,
                on_key_up=keyboard._on_window_key_up,
                on_textinput=keyboard._on_window_textinput)
            self.bind(
                on_key_down=keyboard._on_window_key_down,
                on_key_up=keyboard._on_window_key_up,
                on_textinput=keyboard._on_window_textinput)

        return keyboard

    def release_keyboard(self, target=None):
        '''.. versionadded:: 1.0.4

        Internal method for the widget to release the real-keyboard. Check
        :meth:`request_keyboard` to understand how it works.
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

    def grab_mouse(self):
        '''Grab mouse - so won't leave window

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass

    def ungrab_mouse(self):
        '''Ungrab mouse

        .. versionadded:: 1.10.0

        .. note::
            This feature requires the SDL2 window provider.
        '''
        pass


#: Instance of a :class:`WindowBase` implementation
window_impl = []
if platform == 'linux':
    window_impl += [('egl_rpi', 'window_egl_rpi', 'WindowEglRpi')]
if USE_SDL2:
    window_impl += [('sdl2', 'window_sdl2', 'WindowSDL')]
else:
    window_impl += [
        ('pygame', 'window_pygame', 'WindowPygame')]
if platform == 'linux':
    window_impl += [('x11', 'window_x11', 'WindowX11')]
Window = core_select_lib('window', window_impl, True)

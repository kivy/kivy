"""
GLFW Window
===========

Windowing provider directly based on our own wrapped version of GLFW.

TODO:
    - add pause mode
    - add joysticks input support
    - add drop events support
    - add set_system_cursor() function
    - add get_window_info() function
"""

from os.path import join

from kivy.config import Config
from kivy import kivy_data_dir
from kivy import platform, Logger
from kivy.base import EventLoop
from kivy.resources import resource_find
from kivy.core.window import WindowBase
try:
    from kivy.core.window._window_glfw import WindowGLFWStorage
except ImportError:
    from kivy.core import handle_win_lib_import_error
    handle_win_lib_import_error(
        'window', 'glfw', 'kivy.core.window._window_glfw')
    raise
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

__all__ = ('WindowGLFW', )


class WindowGLFW(WindowBase):

    managed_textinput = True
    gl_backends_ignored = ['sdl2']

    def __init__(self):
        self._win = WindowGLFWStorage()
        super(WindowGLFW, self).__init__()
        self.key_map = {
            65: 97,  # a
            66: 98,  # b
            67: 99,  # c
            68: 100,  # d
            69: 101,  # e
            70: 102,  # f
            71: 103,  # g
            72: 104,  # h
            73: 105,  # i
            74: 106,  # j
            75: 107,  # k
            76: 108,  # l
            77: 109,  # m
            78: 110,  # n
            79: 111,  # o
            80: 112,  # p
            81: 113,  # q
            82: 114,  # r
            83: 115,  # s
            84: 116,  # t
            85: 117,  # u
            86: 118,  # v
            87: 119,  # w
            88: 120,  # x
            89: 121,  # y
            90: 122,  # z
            256: 27,  # escape
            257: 13,  # enter
            258: 9,  # tab
            259: 8,  # backspace
            260: 277,  # insert
            261: 127,  # delete
            262: 275,  # right
            263: 276,  # left
            264: 274,  # down
            265: 273,  # up
            266: 280,  # pageup
            267: 281,  # pagedown
            268: 278,  # home
            269: 279,  # end
            280: 301,  # capslock
            282: 300,  # numlock
            283: 144,  # printscreen
            284: 19,  # pause
            290: 282,  # f1
            291: 283,  # f2
            292: 284,  # f3
            293: 285,  # f4
            294: 286,  # f5
            295: 287,  # f6
            296: 288,  # f7
            297: 289,  # f8
            298: 290,  # f9
            299: 291,  # f10
            300: 292,  # f11
            301: 293,  # f12
            302: 294,  # f13
            303: 295,  # f14
            304: 296,  # f15
            320: 256,  # numpad0
            321: 257,  # numpad1
            322: 258,  # numpad2
            323: 259,  # numpad3
            324: 260,  # numpad4
            325: 261,  # numpad5
            326: 262,  # numpad6
            327: 263,  # numpad7
            328: 264,  # numpad8
            329: 265,  # numpad9
            330: 266,  # numpaddecimal
            331: 267,  # numpaddivide
            332: 268,  # numpadmul
            333: 269,  # numpadsubstract
            334: 270,  # numpadadd
            335: 271,  # numpadenter
            340: 304,  # left shift
            341: 305,  # left control
            342: 308,  # left alt
            343: 309,  # left super
            344: 303,  # right shift
            345: 306,  # right control
            346: 307,  # right alt-gr
            347: 309,  # right super
        }
        self._mouse_buttons_down = set()
        # bindings
        self.bind(minimum_width=self._set_minimum_size,
                  minimum_height=self._set_minimum_size,
                  always_on_top=self._set_always_on_top)

    def create_window(self, *largs):
        if not self.initialized:
            w, h = self.system_size

            if self.position == 'auto':
                pos = None, None
            elif self.position == 'custom':
                pos = self.left, self.top

            self._win.set_window_object(self)
            self.system_size = self._win.setup_window(*pos, w, h,
                                                      self.borderless,
                                                      self.fullscreen)
            self._update_density_and_dpi()
            self._set_minimum_size()
            self._set_always_on_top()
        else:
            self._win.set_window_size(*self.system_size)
            self._win.set_window_border(self.borderless)
            self._win.set_fullscreen_mode(self.fullscreen)

        super(WindowGLFW, self).create_window()

        try:
            filename_icon = self.icon or Config.get('kivy', 'window_icon')
            if filename_icon == '':
                logo_size = 32
                if platform == 'macosx':
                    logo_size = 512
                elif platform == 'win':
                    logo_size = 64
                filename_icon = 'kivy-icon-{}.png'.format(logo_size)
                filename_icon = resource_find(
                        join(kivy_data_dir, 'logo', filename_icon))
            self.set_icon(filename_icon)
        except Exception:
            Logger.exception('Window: cannot set icon')

    def _update_density_and_dpi(self):
        # taken from window_sdl2.py, may be changed using GLFW API
        if platform == 'win':
            from ctypes import windll
            self._density = 1.
            try:
                hwnd = windll.user32.GetActiveWindow()
                self.dpi = float(windll.user32.GetDpiForWindow(hwnd))
            except AttributeError:
                pass
        else:
            self._density = self._win._get_gl_size()[0] / self._size[0]
            if self._is_desktop:
                self.dpi = self._density * 96.

    def get_window_info(self):
        Logger.warning('Window: get_window_info() is not implemented in the '
                       'GLFW window provider.')

    def _set_mouse_pos(self, x, y):
        self.mouse_pos = (
            x * self._density,
            y * self._density
        )

    def _cursor_pos_callback(self, x, y):
        self._set_mouse_pos(x, y)
        if self._mouse_buttons_down:
            self.dispatch('on_mouse_move', x, y, self._modifiers)

    def _cursor_enter_callback(self, eventname):
        self.dispatch(eventname)

    def _mouse_button_callback(self, x, y, mouse_button, eventname):
        if eventname == 'on_mouse_down':
            self._mouse_buttons_down.add(mouse_button)
        else:
            self._mouse_buttons_down.remove(mouse_button)
        self._set_mouse_pos(x, y)
        self.dispatch(eventname, x, y, mouse_button, self._modifiers)

    def _scroll_callback(self, x, y, btn):
        self._set_mouse_pos(x, y)
        self.dispatch('on_mouse_down', x, y, btn, self._modifiers)
        self.dispatch('on_mouse_up', x, y, btn, self._modifiers)

    def _window_pos_callback(self):
        self.dispatch('on_move')

    def _window_size_callback(self, width, height):
        self._size = width, height

    def _window_iconify_callback(self, eventname):
        self.dispatch(eventname)

    def _window_maximize_callback(self, eventname):
        self.dispatch(eventname)

    def _window_focus_callback(self, focus):
        self._focus = bool(focus)

    def _window_refresh_callback(self):
        self.canvas.ask_update()

    def _key_callback(self, eventname, key, scancode, text, modifiers):
        self._modifiers = modifiers
        try:
            key = self.key_map[key]
        except KeyError:
            pass
        if eventname == 'on_key_up':
            self.dispatch(eventname, key, scancode)
        else:
            self.dispatch(eventname, key, scancode, text, modifiers)

    def _char_callback(self, text):
        self.dispatch('on_textinput', text)

    def screenshot(self, *largs, **kwargs):
        filename = super(WindowGLFW, self).screenshot(*largs, **kwargs)
        if filename is None:
            return
        from kivy.graphics.opengl import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE
        width, height = self.size
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        texture = Texture.create(size=(width, height))
        texture.blit_buffer(data)
        texture.save(filename)
        Logger.debug('Window: Screenshot saved at <%s>' % filename)
        return filename

    def set_icon(self, filename):
        image = CoreImage(filename)
        self._win.set_window_icon(image.width, image.height,
                                  image.texture.pixels)

    def set_title(self, title):
        self._win.set_window_title(title)

    def _get_window_pos(self):
        return self._win.get_window_pos()

    def _set_window_pos(self, x, y):
        self._win.set_window_pos(x, y)

    def _set_minimum_size(self, *args):
        minimum_width = self.minimum_width
        minimum_height = self.minimum_height
        if minimum_width and minimum_height:
            self._win.set_minimum_size(minimum_width, minimum_height)
        elif minimum_width or minimum_height:
            Logger.warning(
                'Both Window.minimum_width and Window.minimum_height must be '
                'bigger than 0 for the size restriction to take effect.')

    def _set_always_on_top(self, *args):
        self._win.set_always_on_top(self.always_on_top)

    def maximize(self):
        self._win.maximize_window()

    def minimize(self):
        self._win.minimize_window()

    def restore(self):
        self._win.restore_window()

    def raise_window(self):
        self._win.raise_window()

    def hide(self):
        self._win.hide_window()
        self.dispatch('on_hide')

    def show(self):
        self._win.show_window()
        self.dispatch('on_show')

    def flip(self):
        self._win.flip()

    def mainloop(self):
        self._win.poll()

    def quit(self):
        EventLoop.quit = True

    def close(self):
        self._win.terminate()
        super(WindowGLFW, self).close()
        self.initialized = False

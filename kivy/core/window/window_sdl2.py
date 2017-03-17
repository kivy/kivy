# found a way to include it more easily.
'''
SDL2 Window
===========

Windowing provider directly based on our own wrapped version of SDL.

TODO:
    - fix keys
    - support scrolling
    - clean code
    - manage correctly all sdl events

'''

__all__ = ('WindowSDL2', )

from os.path import join
import sys
from kivy import kivy_data_dir
from kivy.logger import Logger
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import WindowBase
from kivy.core.window._window_sdl2 import _WindowSDL2Storage
from kivy.input.provider import MotionEventProvider
from kivy.input.motionevent import MotionEvent
from kivy.resources import resource_find
from kivy.utils import platform, deprecated
from kivy.compat import unichr
from collections import deque

KMOD_LCTRL = 64
KMOD_RCTRL = 128
KMOD_RSHIFT = 2
KMOD_LSHIFT = 1
KMOD_RALT = 512
KMOD_LALT = 256
KMOD_LMETA = 1024
KMOD_RMETA = 2048

SDLK_SHIFTL = 1073742049
SDLK_SHIFTR = 1073742053
SDLK_LCTRL = 1073742048
SDLK_RCTRL = 1073742052
SDLK_LALT = 1073742050
SDLK_RALT = 1073742054
SDLK_LEFT = 1073741904
SDLK_RIGHT = 1073741903
SDLK_UP = 1073741906
SDLK_DOWN = 1073741905
SDLK_HOME = 1073741898
SDLK_END = 1073741901
SDLK_PAGEUP = 1073741899
SDLK_PAGEDOWN = 1073741902
SDLK_SUPER = 1073742051
SDLK_CAPS = 1073741881
SDLK_INSERT = 1073741897
SDLK_KEYPADNUM = 1073741907
SDLK_KP_DEVIDE = 1073741908
SDLK_KP_MULTIPLY = 1073741909
SDLK_KP_MINUS = 1073741910
SDLK_KP_PLUS = 1073741911
SDLK_KP_ENTER = 1073741912
SDLK_KP_1 = 1073741913
SDLK_KP_2 = 1073741914
SDLK_KP_3 = 1073741915
SDLK_KP_4 = 1073741916
SDLK_KP_5 = 1073741917
SDLK_KP_6 = 1073741918
SDLK_KP_7 = 1073741919
SDLK_KP_8 = 1073741920
SDLK_KP_9 = 1073741921
SDLK_KP_0 = 1073741922
SDLK_KP_DOT = 1073741923
SDLK_F1 = 1073741882
SDLK_F2 = 1073741883
SDLK_F3 = 1073741884
SDLK_F4 = 1073741885
SDLK_F5 = 1073741886
SDLK_F6 = 1073741887
SDLK_F7 = 1073741888
SDLK_F8 = 1073741889
SDLK_F9 = 1073741890
SDLK_F10 = 1073741891
SDLK_F11 = 1073741892
SDLK_F12 = 1073741893
SDLK_F13 = 1073741894
SDLK_F14 = 1073741895
SDLK_F15 = 1073741896


class SDL2MotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.profile = ('pos', )
        self.sx, self.sy = args
        win = EventLoop.window
        super(SDL2MotionEvent, self).depack(args)


class SDL2MotionEventProvider(MotionEventProvider):
    win = None
    q = deque()
    touchmap = {}

    def update(self, dispatch_fn):
        touchmap = self.touchmap
        while True:
            try:
                value = self.q.pop()
            except IndexError:
                return

            action, fid, x, y = value
            y = 1 - y
            if fid not in touchmap:
                touchmap[fid] = me = SDL2MotionEvent('sdl', fid, (x, y))
            else:
                me = touchmap[fid]
                me.move((x, y))
            if action == 'fingerdown':
                dispatch_fn('begin', me)
            elif action == 'fingerup':
                me.update_time_end()
                dispatch_fn('end', me)
                del touchmap[fid]
            else:
                dispatch_fn('update', me)


class WindowSDL(WindowBase):

    _do_resize_ev = None

    def __init__(self, **kwargs):
        self._pause_loop = False
        self._win = _WindowSDL2Storage()
        super(WindowSDL, self).__init__()
        self._mouse_x = self._mouse_y = -1
        self._meta_keys = (KMOD_LCTRL, KMOD_RCTRL, KMOD_RSHIFT,
            KMOD_LSHIFT, KMOD_RALT, KMOD_LALT, KMOD_LMETA,
            KMOD_RMETA)
        self.command_keys = {
                    27: 'escape',
                    9: 'tab',
                    8: 'backspace',
                    13: 'enter',
                    127: 'del',
                    271: 'enter',
                    273: 'up',
                    274: 'down',
                    275: 'right',
                    276: 'left',
                    278: 'home',
                    279: 'end',
                    280: 'pgup',
                    281: 'pgdown'}
        self._mouse_buttons_down = set()
        self.key_map = {SDLK_LEFT: 276, SDLK_RIGHT: 275, SDLK_UP: 273,
                        SDLK_DOWN: 274, SDLK_HOME: 278, SDLK_END: 279,
                        SDLK_PAGEDOWN: 281, SDLK_PAGEUP: 280, SDLK_SHIFTR: 303,
                        SDLK_SHIFTL: 304, SDLK_SUPER: 309, SDLK_LCTRL: 305,
                        SDLK_RCTRL: 306, SDLK_LALT: 308, SDLK_RALT: 307,
                        SDLK_CAPS: 301, SDLK_INSERT: 277, SDLK_F1: 282,
                        SDLK_F2: 283, SDLK_F3: 284, SDLK_F4: 285, SDLK_F5: 286,
                        SDLK_F6: 287, SDLK_F7: 288, SDLK_F8: 289, SDLK_F9: 290,
                        SDLK_F10: 291, SDLK_F11: 292, SDLK_F12: 293,
                        SDLK_F13: 294, SDLK_F14: 295, SDLK_F15: 296,
                        SDLK_KEYPADNUM: 300, SDLK_KP_DEVIDE: 267,
                        SDLK_KP_MULTIPLY: 268, SDLK_KP_MINUS: 269,
                        SDLK_KP_PLUS: 270, SDLK_KP_ENTER: 271,
                        SDLK_KP_DOT: 266, SDLK_KP_0: 256, SDLK_KP_1: 257,
                        SDLK_KP_2: 258, SDLK_KP_3: 259, SDLK_KP_4: 260,
                        SDLK_KP_5: 261, SDLK_KP_6: 262, SDLK_KP_7: 263,
                        SDLK_KP_8: 264, SDLK_KP_9: 265}
        if platform == 'ios':
            # XXX ios keyboard suck, when backspace is hit, the delete
            # keycode is sent. fix it.
            self.key_map[127] = 8
        elif platform == 'android':
            # map android back button to escape
            self.key_map[1073742094] = 27

        self.bind(minimum_width=self._set_minimum_size,
                  minimum_height=self._set_minimum_size)

        self.bind(allow_screensaver=self._set_allow_screensaver)

    def _set_minimum_size(self, *args):
        minimum_width = self.minimum_width
        minimum_height = self.minimum_height
        if minimum_width and minimum_height:
            self._win.set_minimum_size(minimum_width, minimum_height)
        elif minimum_width or minimum_height:
            Logger.warning(
                'Both Window.minimum_width and Window.minimum_height must be '
                'bigger than 0 for the size restriction to take effect.')

    def _set_allow_screensaver(self, *args):
        self._win.set_allow_screensaver(self.allow_screensaver)

    def _event_filter(self, action):
        from kivy.app import App
        if action == 'app_terminating':
            EventLoop.quit = True
            self.close()

        elif action == 'app_lowmemory':
            self.dispatch('on_memorywarning')

        elif action == 'app_willenterbackground':
            from kivy.base import stopTouchApp
            app = App.get_running_app()
            if not app:
                Logger.info('WindowSDL: No running App found, exit.')
                stopTouchApp()
                return 0

            if not app.dispatch('on_pause'):
                Logger.info(
                    'WindowSDL: App doesn\'t support pause mode, stop.')
                stopTouchApp()
                return 0

            self._pause_loop = True

        elif action == 'app_didenterforeground':
            # on iOS, the did enter foreground is launched at the start
            # of the application. in our case, we want it only when the app
            # is resumed
            if self._pause_loop:
                self._pause_loop = False
                app = App.get_running_app()
                app.dispatch('on_resume')

        return 0

    def create_window(self, *largs):
        if self._fake_fullscreen:
            if not self.borderless:
                self.fullscreen = self._fake_fullscreen = False
            elif not self.fullscreen or self.fullscreen == 'auto':
                self.borderless = self._fake_fullscreen = False
        if self.fullscreen == 'fake':
            self.borderless = self._fake_fullscreen = True
            Logger.warning("The 'fake' fullscreen option has been "
                           "deprecated, use Window.borderless or the "
                           "borderless Config option instead.")

        if not self.initialized:

            if self.position == 'auto':
                pos = None, None
            elif self.position == 'custom':
                pos = self.left, self.top

            # ensure we have an event filter
            self._win.set_event_filter(self._event_filter)

            # setup window
            w, h = self.system_size
            resizable = Config.getboolean('graphics', 'resizable')
            state = (Config.get('graphics', 'window_state')
                     if self._is_desktop else None)
            self.system_size = _size = self._win.setup_window(
                pos[0], pos[1], w, h, self.borderless,
                self.fullscreen, resizable, state)

            # calculate density
            sz = self._win._get_gl_size()[0]
            self._density = density = sz / _size[0]
            if self._is_desktop and self.size[0] != _size[0]:
                self.dpi = density * 96.

            # never stay with a None pos, application using w.center
            # will be fired.
            self._pos = (0, 0)
            self._set_minimum_size()
            self._set_allow_screensaver()

            if state == 'hidden':
                self._focus = False
        else:
            w, h = self.system_size
            self._win.resize_window(w, h)
            self._win.set_border_state(self.borderless)
            self._win.set_fullscreen_mode(self.fullscreen)

        super(WindowSDL, self).create_window()
        # set mouse visibility
        self._set_cursor_state(self.show_cursor)

        if self.initialized:
            return

        # auto add input provider
        Logger.info('Window: auto add sdl2 input provider')
        from kivy.base import EventLoop
        SDL2MotionEventProvider.win = self
        EventLoop.add_input_provider(SDL2MotionEventProvider('sdl', ''))

        # set window icon before calling set_mode
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
        except:
            Logger.exception('Window: cannot set icon')

    def close(self):
        self._win.teardown_window()
        self.dispatch('on_close')

    def maximize(self):
        if self._is_desktop:
            self._win.maximize_window()
        else:
            Logger.warning('Window: maximize() is used only on desktop OSes.')

    def minimize(self):
        if self._is_desktop:
            self._win.minimize_window()
        else:
            Logger.warning('Window: minimize() is used only on desktop OSes.')

    def restore(self):
        if self._is_desktop:
            self._win.restore_window()
        else:
            Logger.warning('Window: restore() is used only on desktop OSes.')

    def hide(self):
        if self._is_desktop:
            self._win.hide_window()
        else:
            Logger.warning('Window: hide() is used only on desktop OSes.')

    def show(self):
        if self._is_desktop:
            self._win.show_window()
        else:
            Logger.warning('Window: show() is used only on desktop OSes.')

    def raise_window(self):
        if self._is_desktop:
            self._win.raise_window()
        else:
            Logger.warning('Window: show() is used only on desktop OSes.')

    @deprecated
    def toggle_fullscreen(self):
        if self.fullscreen in (True, 'auto'):
            self.fullscreen = False
        else:
            self.fullscreen = 'auto'

    def set_title(self, title):
        self._win.set_window_title(title)

    def set_icon(self, filename):
        self._win.set_window_icon(str(filename))

    def screenshot(self, *largs, **kwargs):
        filename = super(WindowSDL, self).screenshot(*largs, **kwargs)
        if filename is None:
            return

        from kivy.graphics.opengl import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE
        width, height = self.size
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        self._win.save_bytes_in_png(filename, data, width, height)
        Logger.debug('Window: Screenshot saved at <%s>' % filename)
        return filename

    def flip(self):
        self._win.flip()
        super(WindowSDL, self).flip()

    def _get_window_pos(self):
        return self._win.get_window_pos()

    def _set_window_pos(self, x, y):
        self._win.set_window_pos(x, y)

    def _set_cursor_state(self, value):
        self._win._set_cursor_state(value)

    def _fix_mouse_pos(self, x, y):
        y -= 1
        self.mouse_pos = (x * self._density,
                          (self.system_size[1] - y) * self._density)
        return x, y

    def _mainloop(self):
        EventLoop.idle()

        # for android/iOS, we don't want to have any event nor executing our
        # main loop while the pause is going on. This loop wait any event (not
        # handled by the event filter), and remove them from the queue.
        # Nothing happen during the pause on iOS, except gyroscope value sent
        # over joystick. So it's safe.
        while self._pause_loop:
            self._win.wait_event()
            if not self._pause_loop:
                break
            self._win.poll()

        while True:
            event = self._win.poll()
            if event is False:
                break
            if event is None:
                continue

            action, args = event[0], event[1:]
            if action == 'quit':
                if self.dispatch('on_request_close'):
                    continue
                EventLoop.quit = True
                self.close()
                break

            elif action in ('fingermotion', 'fingerdown', 'fingerup'):
                # for finger, pass the raw event to SDL motion event provider
                # XXX this is problematic. On OSX, it generates touches with 0,
                # 0 coordinates, at the same times as mouse. But it works.
                # We have a conflict of using either the mouse or the finger.
                # Right now, we have no mechanism that we could use to know
                # which is the preferred one for the application.
                if platform in ('ios', 'android'):
                    SDL2MotionEventProvider.q.appendleft(event)
                pass

            elif action == 'mousemotion':
                x, y = args
                x, y = self._fix_mouse_pos(x, y)
                self._mouse_x = x
                self._mouse_y = y
                # don't dispatch motion if no button are pressed
                if len(self._mouse_buttons_down) == 0:
                    continue
                self._mouse_meta = self.modifiers
                self.dispatch('on_mouse_move', x, y, self.modifiers)

            elif action in ('mousebuttondown', 'mousebuttonup'):
                x, y, button = args
                x, y = self._fix_mouse_pos(x, y)
                btn = 'left'
                if button == 3:
                    btn = 'right'
                elif button == 2:
                    btn = 'middle'
                eventname = 'on_mouse_down'
                self._mouse_buttons_down.add(button)
                if action == 'mousebuttonup':
                    eventname = 'on_mouse_up'
                    self._mouse_buttons_down.remove(button)
                self._mouse_x = x
                self._mouse_y = y
                self.dispatch(eventname, x, y, btn, self.modifiers)
            elif action.startswith('mousewheel'):
                self._update_modifiers()
                x, y, button = args
                btn = 'scrolldown'
                if action.endswith('up'):
                    btn = 'scrollup'
                elif action.endswith('right'):
                    btn = 'scrollright'
                elif action.endswith('left'):
                    btn = 'scrollleft'

                self._mouse_meta = self.modifiers
                self._mouse_btn = btn
                # times = x if y == 0 else y
                # times = min(abs(times), 100)
                # for k in range(times):
                self._mouse_down = True
                self.dispatch('on_mouse_down',
                    self._mouse_x, self._mouse_y, btn, self.modifiers)
                self._mouse_down = False
                self.dispatch('on_mouse_up',
                    self._mouse_x, self._mouse_y, btn, self.modifiers)

            elif action == 'dropfile':
                dropfile = args
                self.dispatch('on_dropfile', dropfile[0])
            # video resize
            elif action == 'windowresized':
                self._size = self._win.window_size
                # don't use trigger here, we want to delay the resize event
                ev = self._do_resize_ev
                if ev is None:
                    ev = Clock.schedule_once(self._do_resize, .1)
                    self._do_resize_ev = ev
                else:
                    ev()

            elif action == 'windowresized':
                self.canvas.ask_update()

            elif action == 'windowrestored':
                self.dispatch('on_restore')
                self.canvas.ask_update()

            elif action == 'windowexposed':
                self.canvas.ask_update()

            elif action == 'windowminimized':
                self.dispatch('on_minimize')
                if Config.getboolean('kivy', 'pause_on_minimize'):
                    self.do_pause()

            elif action == 'windowmaximized':
                self.dispatch('on_maximize')

            elif action == 'windowhidden':
                self.dispatch('on_hide')

            elif action == 'windowshown':
                self.dispatch('on_show')

            elif action == 'windowfocusgained':
                self._focus = True

            elif action == 'windowfocuslost':
                self._focus = False

            elif action == 'windowenter':
                self.dispatch('on_cursor_enter')

            elif action == 'windowleave':
                self.dispatch('on_cursor_leave')

            elif action == 'joyaxismotion':
                stickid, axisid, value = args
                self.dispatch('on_joy_axis', stickid, axisid, value)
            elif action == 'joyhatmotion':
                stickid, hatid, value = args
                self.dispatch('on_joy_hat', stickid, hatid, value)
            elif action == 'joyballmotion':
                stickid, ballid, xrel, yrel = args
                self.dispatch('on_joy_ball', stickid, ballid, xrel, yrel)
            elif action == 'joybuttondown':
                stickid, buttonid = args
                self.dispatch('on_joy_button_down', stickid, buttonid)
            elif action == 'joybuttonup':
                stickid, buttonid = args
                self.dispatch('on_joy_button_up', stickid, buttonid)

            elif action in ('keydown', 'keyup'):
                mod, key, scancode, kstr = args

                try:
                    key = self.key_map[key]
                except KeyError:
                    pass

                if action == 'keydown':
                    self._update_modifiers(mod, key)
                else:
                    # ignore the key, it has been released
                    self._update_modifiers(mod)

                # if mod in self._meta_keys:
                if (key not in self._modifiers and
                        key not in self.command_keys.keys()):
                    try:
                        kstr_chr = unichr(key)
                        try:
                            # On android, there is no 'encoding' attribute.
                            # On other platforms, if stdout is redirected,
                            # 'encoding' may be None
                            encoding = getattr(sys.stdout, 'encoding',
                                               'utf8') or 'utf8'
                            kstr_chr.encode(encoding)
                            kstr = kstr_chr
                        except UnicodeError:
                            pass
                    except ValueError:
                        pass
                # if 'shift' in self._modifiers and key\
                #        not in self.command_keys.keys():
                #    return

                if action == 'keyup':
                    self.dispatch('on_key_up', key, scancode)
                    continue

                # don't dispatch more key if down event is accepted
                if self.dispatch('on_key_down', key,
                                 scancode, kstr,
                                 self.modifiers):
                    continue
                self.dispatch('on_keyboard', key,
                              scancode, kstr,
                              self.modifiers)

            elif action == 'textinput':
                text = args[0]
                self.dispatch('on_textinput', text)

            # unhandled event !
            else:
                Logger.trace('WindowSDL: Unhandled event %s' % str(event))

    def _do_resize(self, dt):
        Logger.debug('Window: Resize window to %s' % str(self.size))
        self._win.resize_window(*self._size)
        self.dispatch('on_resize', *self.size)

    def do_pause(self):
        # should go to app pause mode (desktop style)
        from kivy.app import App
        from kivy.base import stopTouchApp
        app = App.get_running_app()
        if not app:
            Logger.info('WindowSDL: No running App found, exit.')
            stopTouchApp()
            return

        if not app.dispatch('on_pause'):
            Logger.info('WindowSDL: App doesn\'t support pause mode, stop.')
            stopTouchApp()
            return

        # XXX FIXME wait for sdl resume
        while True:
            event = self._win.poll()
            if event is False:
                continue
            if event is None:
                continue

            action, args = event[0], event[1:]
            if action == 'quit':
                EventLoop.quit = True
                self.close()
                break
            elif action == 'app_willenterforeground':
                break
            elif action == 'windowrestored':
                break

        app.dispatch('on_resume')

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        # self.dispatch('on_resize', *self.size)

        while not EventLoop.quit and EventLoop.status == 'started':
            try:
                self._mainloop()
            except BaseException as inst:
                # use exception manager first
                r = ExceptionManager.handle_exception(inst)
                if r == ExceptionManager.RAISE:
                    stopTouchApp()
                    raise
                else:
                    pass

    #
    # Pygame wrapper
    #
    def _update_modifiers(self, mods=None, key=None):
        # Available mod, from dir(pygame)
        # 'KMOD_ALT', 'KMOD_CAPS', 'KMOD_CTRL', 'KMOD_LALT',
        # 'KMOD_LCTRL', 'KMOD_LMETA', 'KMOD_LSHIFT', 'KMOD_META',
        # 'KMOD_MODE', 'KMOD_NONE'
        if mods is None and key is None:
            return
        modifiers = set()

        if mods is not None:
            if mods & (KMOD_RSHIFT | KMOD_LSHIFT):
                modifiers.add('shift')
            if mods & (KMOD_RALT | KMOD_LALT):
                modifiers.add('alt')
            if mods & (KMOD_RCTRL | KMOD_LCTRL):
                modifiers.add('ctrl')
            if mods & (KMOD_RMETA | KMOD_LMETA):
                modifiers.add('meta')

        if key is not None:
            if key in (KMOD_RSHIFT, KMOD_LSHIFT):
                modifiers.add('shift')
            if key in (KMOD_RALT, KMOD_LALT):
                modifiers.add('alt')
            if key in (KMOD_RCTRL, KMOD_LCTRL):
                modifiers.add('ctrl')
            if key in (KMOD_RMETA, KMOD_LMETA):
                modifiers.add('meta')

        self._modifiers = list(modifiers)
        return

    def request_keyboard(self, callback, target, input_type='text'):
        self._sdl_keyboard = super(WindowSDL, self).\
            request_keyboard(callback, target, input_type)
        self._win.show_keyboard(self._system_keyboard, self.softinput_mode)
        Clock.schedule_interval(self._check_keyboard_shown, 1 / 5.)
        return self._sdl_keyboard

    def release_keyboard(self, *largs):
        super(WindowSDL, self).release_keyboard(*largs)
        self._win.hide_keyboard()
        self._sdl_keyboard = None
        return True

    def _check_keyboard_shown(self, dt):
        if self._sdl_keyboard is None:
            return False
        if not self._win.is_keyboard_shown():
            self._sdl_keyboard.release()

    def map_key(self, original_key, new_key):
        self.key_map[original_key] = new_key

    def unmap_key(self, key):
        if key in self.key_map:
            del self.key_map[key]

    def grab_mouse(self):
        self._win.grab_mouse(True)

    def ungrab_mouse(self):
        self._win.grab_mouse(False)

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

import sys
from os.path import join
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


class SDL2MotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.profile = ('pos', )
        self.sx, self.sy = args
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
            x = x / 32768.
            y = 1 - (y / 32768.)
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

    def __init__(self, **kwargs):
        self._win = _WindowSDL2Storage()
        super(WindowSDL, self).__init__()
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

            # setup !
            w, h = self._size
            resizable = Config.getboolean('graphics', 'resizable')
            gl_size = self._win.setup_window(pos[0], pos[1], w, h,
                                             self.borderless, self.fullscreen,
                                             resizable)
            # never stay with a None pos, application using w.center
            # will be fired.
            self._pos = (0, 0)
        else:
            w, h = self._size
            self._win.resize_window(w, h)
            self._win.set_border_state(self.borderless)
            self._win.set_fullscreen_mode(self.fullscreen)

        super(WindowSDL, self).create_window()

        # auto add input provider
        Logger.info('Window: auto add sdl input provider')
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

    @deprecated
    def toggle_fullscreen(self):
        if self.fullscreen in (True, 'auto'):
            self.fullscreen = False
        else:
            self.fullscreen = 'auto'

    def set_title(self, title):
        self._win.set_window_title(title)

    def set_icon(self, filename):
        self._win.set_window_icon(filename)

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

    def _mainloop(self):
        EventLoop.idle()

        while True:
            event = self._win.poll()
            if event is False:
                break
            if event is None:
                continue

            action, args = event[0], event[1:]
            if action == 'quit':
                EventLoop.quit = True
                self.close()
                break

            elif action in ('fingermotion', 'fingerdown', 'fingerup'):
                # for finger, pass the raw event to SDL motion event provider
                SDL2MotionEventProvider.q.appendleft(event)

            if action == 'mousemotion':
                x, y = args
                self.mouse_pos = x, self.system_size[1] - y
                # don't dispatch motion if no button are pressed
                if len(self._mouse_buttons_down) == 0:
                    continue
                self._mouse_x = x
                self._mouse_y = y
                self._mouse_meta = self.modifiers
                self.dispatch('on_mouse_move', x, y, self.modifiers)

            elif action in ('mousebuttondown', 'mousebuttonup'):
                x, y, button = args
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
                #times = x if y == 0 else y
                #times = min(abs(times), 100)
                #for k in range(times):
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
                self._size = args
                # don't use trigger here, we want to delay the resize event
                cb = self._do_resize
                Clock.unschedule(cb)
                Clock.schedule_once(cb, .1)

            elif action == 'windowresized':
                self.canvas.ask_update()

            elif action == 'windowrestored':
                self.canvas.ask_update()

            elif action == 'windowminimized':
                if Config.getboolean('kivy', 'pause_on_minimize'):
                    self.do_pause()

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
                if mod in self._meta_keys:
                    try:
                        kstr = unichr(key)
                    except ValueError:
                        pass

                key_swap = {
                            SDLK_LEFT: 276,
                            SDLK_RIGHT: 275,
                            SDLK_UP: 273,
                            SDLK_DOWN: 274,
                            SDLK_HOME: 278,
                            SDLK_END: 279,
                            SDLK_PAGEDOWN: 281,
                            SDLK_PAGEUP: 280,
                            SDLK_SHIFTL: 303,
                            SDLK_SHIFTR: 304,
                            SDLK_LCTRL: KMOD_LCTRL,
                            SDLK_RCTRL: KMOD_RCTRL,
                            SDLK_LALT: KMOD_LALT,
                            SDLK_RALT: KMOD_RALT}

                if platform == 'ios':
                    # XXX ios keyboard suck, when backspace is hit, the delete
                    # keycode is sent. fix it.
                    key_swap[127] = 8  # back

                try:
                    key = key_swap[key]
                except KeyError:
                    pass

                self._update_modifiers(mod)
                if 'shift' in self._modifiers and key\
                        not in self.command_keys.keys():
                    return

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
                key = args[0][0]
                # XXX on IOS, keydown/up don't send unicode anymore.
                # With latest sdl, the text is sent over textinput
                # Right now, redo keydown/up, but we need to seperate both call
                # too. (and adapt on_key_* API.)
                self.dispatch('on_key_down', key, None, args[0],
                              self.modifiers)
                self.dispatch('on_keyboard', None, None, args[0],
                              self.modifiers)
                self.dispatch('on_key_up', key, None, args[0],
                              self.modifiers)
        #    # video resize
        #    elif event.type == pygame.VIDEORESIZE:
        #        self._size = event.size
        #        # don't use trigger here, we want to delay the resize event
        #        cb = self._do_resize
        #        Clock.unschedule(cb)
        #        Clock.schedule_once(cb, .1)

        #    elif event.type == pygame.VIDEOEXPOSE:
        #        self.canvas.ask_update()

        #    # ignored event
        #    elif event.type == pygame.ACTIVEEVENT:
        #        pass

        #    # unhandled event !
        #    else:
        #        Logger.debug('WinPygame: Unhandled event %s' % str(event))

    def _do_resize(self, dt):
        Logger.debug('Window: Resize window to %s' % str(self._size))
        self._win.resize_display_mode(*self._size)
        self.dispatch('on_resize', *self._size)

    def do_pause(self):
        # should go to app pause mode.
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
            elif action == 'windowrestored':
                break

        app.dispatch('on_resume')

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        self.dispatch('on_resize', *self.size)

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

        # force deletion of window
        self._win.teardown_window()

    #
    # Pygame wrapper
    #
    def _update_modifiers(self, mods=None):
        # Available mod, from dir(pygame)
        # 'KMOD_ALT', 'KMOD_CAPS', 'KMOD_CTRL', 'KMOD_LALT',
        # 'KMOD_LCTRL', 'KMOD_LMETA', 'KMOD_LSHIFT', 'KMOD_META',
        # 'KMOD_MODE', 'KMOD_NONE'
        if mods is None:
            return
        self._modifiers = []

        if mods & (KMOD_RSHIFT | KMOD_LSHIFT):
            self._modifiers.append('shift')
        if mods & (KMOD_RALT | KMOD_LALT):
            self._modifiers.append('alt')
        if mods & (KMOD_RCTRL | KMOD_LCTRL):
            self._modifiers.append('ctrl')
        if mods & (KMOD_RMETA | KMOD_LMETA):
            self._modifiers.append('meta')
        return

    def request_keyboard(self, callback, target, input_type='text'):
        self._sdl_keyboard = super(WindowSDL, self).\
            request_keyboard(callback, target, input_type)
        self._win.show_keyboard()
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


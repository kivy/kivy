'''
Window Pygame: windowing provider based on Pygame

.. warning::

    Pygame has been deprecated and will be removed in the release after Kivy
    1.11.0.
'''

__all__ = ('WindowPygame', )

# fail early if possible
import pygame

from kivy.compat import PY2
from kivy.core.window import WindowBase
from kivy.core import CoreCriticalException
from os import environ
from os.path import exists, join
from kivy.config import Config
from kivy import kivy_data_dir
from kivy.base import ExceptionManager
from kivy.logger import Logger
from kivy.base import stopTouchApp, EventLoop
from kivy.utils import platform, deprecated
from kivy.resources import resource_find

try:
    android = None
    if platform == 'android':
        import android
except ImportError:
    pass

# late binding
glReadPixels = GL_RGBA = GL_UNSIGNED_BYTE = None


class WindowPygame(WindowBase):

    @deprecated(
        msg='Pygame has been deprecated and will be removed after 1.11.0')
    def __init__(self, *largs, **kwargs):
        super(WindowPygame, self).__init__(*largs, **kwargs)

    def create_window(self, *largs):
        # ensure the mouse is still not up after window creation, otherwise, we
        # have some weird bugs
        self.dispatch('on_mouse_up', 0, 0, 'all', [])

        # force display to show (available only for fullscreen)
        displayidx = Config.getint('graphics', 'display')
        if 'SDL_VIDEO_FULLSCREEN_HEAD' not in environ and displayidx != -1:
            environ['SDL_VIDEO_FULLSCREEN_HEAD'] = '%d' % displayidx

        # init some opengl, same as before.
        self.flags = pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF

        # right now, activate resizable window only on linux.
        # on window / macosx, the opengl context is lost, and we need to
        # reconstruct everything. Check #168 for a state of the work.
        if platform in ('linux', 'macosx', 'win') and \
                Config.getboolean('graphics', 'resizable'):
            self.flags |= pygame.RESIZABLE

        try:
            pygame.display.init()
        except pygame.error as e:
            raise CoreCriticalException(e.message)

        multisamples = Config.getint('graphics', 'multisamples')

        if multisamples > 0:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES,
                                            multisamples)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 1)
        pygame.display.set_caption(self.title)

        if self.position == 'auto':
            self._pos = None
        elif self.position == 'custom':
            self._pos = self.left, self.top
        else:
            raise ValueError('position token in configuration accept only '
                             '"auto" or "custom"')

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

        if self.fullscreen == 'fake' or self.borderless:
            Logger.debug('WinPygame: Set window to borderless mode.')

            self.flags |= pygame.NOFRAME
            # If no position set in borderless mode, we always need
            # to set the position. So use 0, 0.
            if self._pos is None:
                self._pos = (0, 0)
            environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        elif self.fullscreen in ('auto', True):
            Logger.debug('WinPygame: Set window to fullscreen mode')
            self.flags |= pygame.FULLSCREEN

        elif self._pos is not None:
            environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        # never stay with a None pos, application using w.center will be fired.
        self._pos = (0, 0)

        # prepare keyboard
        repeat_delay = int(Config.get('kivy', 'keyboard_repeat_delay'))
        repeat_rate = float(Config.get('kivy', 'keyboard_repeat_rate'))
        pygame.key.set_repeat(repeat_delay, int(1000. / repeat_rate))

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

        # try to use mode with multisamples
        try:
            self._pygame_set_mode()
        except pygame.error as e:
            if multisamples:
                Logger.warning('WinPygame: Video: failed (multisamples=%d)' %
                               multisamples)
                Logger.warning('WinPygame: trying without antialiasing')
                pygame.display.gl_set_attribute(
                    pygame.GL_MULTISAMPLEBUFFERS, 0)
                pygame.display.gl_set_attribute(
                    pygame.GL_MULTISAMPLESAMPLES, 0)
                multisamples = 0
                try:
                    self._pygame_set_mode()
                except pygame.error as e:
                    raise CoreCriticalException(e.message)
            else:
                raise CoreCriticalException(e.message)

        if pygame.RESIZABLE & self.flags:
            self._pygame_set_mode()

        info = pygame.display.Info()
        self._size = (info.current_w, info.current_h)
        # self.dispatch('on_resize', *self._size)

        # in order to debug futur issue with pygame/display, let's show
        # more debug output.
        Logger.debug('Window: Display driver ' + pygame.display.get_driver())
        Logger.debug('Window: Actual window size: %dx%d',
                     info.current_w, info.current_h)
        if platform != 'android':
            # unsupported platform, such as android that doesn't support
            # gl_get_attribute.
            Logger.debug(
                'Window: Actual color bits r%d g%d b%d a%d',
                pygame.display.gl_get_attribute(pygame.GL_RED_SIZE),
                pygame.display.gl_get_attribute(pygame.GL_GREEN_SIZE),
                pygame.display.gl_get_attribute(pygame.GL_BLUE_SIZE),
                pygame.display.gl_get_attribute(pygame.GL_ALPHA_SIZE))
            Logger.debug(
                'Window: Actual depth bits: %d',
                pygame.display.gl_get_attribute(pygame.GL_DEPTH_SIZE))
            Logger.debug(
                'Window: Actual stencil bits: %d',
                pygame.display.gl_get_attribute(pygame.GL_STENCIL_SIZE))
            Logger.debug(
                'Window: Actual multisampling samples: %d',
                pygame.display.gl_get_attribute(pygame.GL_MULTISAMPLESAMPLES))
        super(WindowPygame, self).create_window()

        # set mouse visibility
        self._set_cursor_state(self.show_cursor)

        # if we are on android platform, automatically create hooks
        if android:
            from kivy.support import install_android
            install_android()

    def close(self):
        pygame.display.quit()
        super(WindowPygame, self).close()

    def on_title(self, instance, value):
        if self.initialized:
            pygame.display.set_caption(self.title)

    def set_icon(self, filename):
        if not exists(filename):
            return False
        try:
            if platform == 'win':
                try:
                    if self._set_icon_win(filename):
                        return True
                except:
                    # fallback on standard loading then.
                    pass

            # for all others platform, or if the ico is not available, use the
            # default way to set it.
            self._set_icon_standard(filename)
            super(WindowPygame, self).set_icon(filename)
        except:
            Logger.exception('WinPygame: unable to set icon')

    def _set_icon_standard(self, filename):
        if PY2:
            try:
                im = pygame.image.load(filename)
            except UnicodeEncodeError:
                im = pygame.image.load(filename.encode('utf8'))
        else:
            im = pygame.image.load(filename)
        if im is None:
            raise Exception('Unable to load window icon (not found)')
        pygame.display.set_icon(im)

    def _set_icon_win(self, filename):
        # ensure the window ico is ended by ico
        if not filename.endswith('.ico'):
            filename = '{}.ico'.format(filename.rsplit('.', 1)[0])
        if not exists(filename):
            return False

        import win32api
        import win32gui
        import win32con
        hwnd = pygame.display.get_wm_info()['window']
        icon_big = win32gui.LoadImage(
            None, filename, win32con.IMAGE_ICON,
            48, 48, win32con.LR_LOADFROMFILE)
        icon_small = win32gui.LoadImage(
            None, filename, win32con.IMAGE_ICON,
            16, 16, win32con.LR_LOADFROMFILE)
        win32api.SendMessage(
            hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, icon_small)
        win32api.SendMessage(
            hwnd, win32con.WM_SETICON, win32con.ICON_BIG, icon_big)
        return True

    def _set_cursor_state(self, value):
        pygame.mouse.set_visible(value)

    def screenshot(self, *largs, **kwargs):
        global glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE
        filename = super(WindowPygame, self).screenshot(*largs, **kwargs)
        if filename is None:
            return None
        if glReadPixels is None:
            from kivy.graphics.opengl import (glReadPixels, GL_RGBA,
                                              GL_UNSIGNED_BYTE)
        width, height = self.system_size
        data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        data = bytes(bytearray(data))
        surface = pygame.image.fromstring(data, (width, height), 'RGBA', True)
        pygame.image.save(surface, filename)
        Logger.debug('Window: Screenshot saved at <%s>' % filename)
        return filename

    def flip(self):
        pygame.display.flip()
        super(WindowPygame, self).flip()

    def mainloop(self):
        for event in pygame.event.get():

            # kill application (SIG_TERM)
            if event.type == pygame.QUIT:
                if self.dispatch('on_request_close'):
                    continue
                EventLoop.quit = True
                self.close()

            # mouse move
            elif event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                self.mouse_pos = x, self.system_size[1] - y
                # don't dispatch motion if no button are pressed
                if event.buttons == (0, 0, 0):
                    continue
                self._mouse_x = x
                self._mouse_y = y
                self._mouse_meta = self.modifiers
                self.dispatch('on_mouse_move', x, y, self.modifiers)

            # mouse action
            elif event.type in (pygame.MOUSEBUTTONDOWN,
                                pygame.MOUSEBUTTONUP):
                self._pygame_update_modifiers()
                x, y = event.pos
                btn = 'left'
                if event.button == 3:
                    btn = 'right'
                elif event.button == 2:
                    btn = 'middle'
                elif event.button == 4:
                    btn = 'scrolldown'
                elif event.button == 5:
                    btn = 'scrollup'
                elif event.button == 6:
                    btn = 'scrollright'
                elif event.button == 7:
                    btn = 'scrollleft'
                eventname = 'on_mouse_down'
                if event.type == pygame.MOUSEBUTTONUP:
                    eventname = 'on_mouse_up'
                self._mouse_x = x
                self._mouse_y = y
                self._mouse_meta = self.modifiers
                self._mouse_btn = btn
                self._mouse_down = eventname == 'on_mouse_down'
                self.dispatch(eventname, x, y, btn, self.modifiers)

            # joystick action
            elif event.type == pygame.JOYAXISMOTION:
                self.dispatch('on_joy_axis', event.joy, event.axis,
                                event.value)

            elif event.type == pygame.JOYHATMOTION:
                self.dispatch('on_joy_hat', event.joy, event.hat, event.value)

            elif event.type == pygame.JOYBALLMOTION:
                self.dispatch('on_joy_ball', event.joy, event.ballid,
                            event.rel[0], event.rel[1])

            elif event.type == pygame.JOYBUTTONDOWN:
                self.dispatch('on_joy_button_down', event.joy, event.button)

            elif event.type == pygame.JOYBUTTONUP:
                self.dispatch('on_joy_button_up', event.joy, event.button)

            # keyboard action
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                self._pygame_update_modifiers(event.mod)
                # atm, don't handle keyup
                if event.type == pygame.KEYUP:
                    self.dispatch('on_key_up', event.key,
                                  event.scancode)
                    continue

                # don't dispatch more key if down event is accepted
                if self.dispatch('on_key_down', event.key,
                                 event.scancode, event.unicode,
                                 self.modifiers):
                    continue
                self.dispatch('on_keyboard', event.key,
                              event.scancode, event.unicode,
                              self.modifiers)

            # video resize
            elif event.type == pygame.VIDEORESIZE:
                self._size = event.size
                self.update_viewport()

            elif event.type == pygame.VIDEOEXPOSE:
                self.canvas.ask_update()

            # ignored event
            elif event.type == pygame.ACTIVEEVENT:
                pass

            # drop file (pygame patch needed)
            elif event.type == pygame.USEREVENT and \
                    hasattr(pygame, 'USEREVENT_DROPFILE') and \
                    event.code == pygame.USEREVENT_DROPFILE:
                drop_x, drop_y = pygame.mouse.get_pos()
                self.dispatch('on_drop_file', event.filename, drop_x, drop_y)

            '''
            # unhandled event !
            else:
                Logger.debug('WinPygame: Unhandled event %s' % str(event))
            '''
        if not pygame.display.get_active():
            pygame.time.wait(100)

    #
    # Pygame wrapper
    #
    def _pygame_set_mode(self, size=None):
        if size is None:
            size = self.size
        if self.fullscreen == 'auto':
            pygame.display.set_mode((0, 0), self.flags)
        else:
            pygame.display.set_mode(size, self.flags)

    def _pygame_update_modifiers(self, mods=None):
        # Available mod, from dir(pygame)
        # 'KMOD_ALT', 'KMOD_CAPS', 'KMOD_CTRL', 'KMOD_LALT',
        # 'KMOD_LCTRL', 'KMOD_LMETA', 'KMOD_LSHIFT', 'KMOD_META',
        # 'KMOD_MODE', 'KMOD_NONE'
        if mods is None:
            mods = pygame.key.get_mods()
        self._modifiers = []
        if mods & (pygame.KMOD_SHIFT | pygame.KMOD_LSHIFT):
            self._modifiers.append('shift')
        if mods & (pygame.KMOD_ALT | pygame.KMOD_LALT):
            self._modifiers.append('alt')
        if mods & (pygame.KMOD_CTRL | pygame.KMOD_LCTRL):
            self._modifiers.append('ctrl')
        if mods & (pygame.KMOD_META | pygame.KMOD_LMETA):
            self._modifiers.append('meta')

    def request_keyboard(
            self, callback, target, input_type='text', keyboard_suggestions=True
    ):
        keyboard = super(WindowPygame, self).request_keyboard(
            callback, target, input_type, keyboard_suggestions)
        if android and not self.allow_vkeyboard:
            android.show_keyboard(target, input_type)
        return keyboard

    def release_keyboard(self, *largs):
        super(WindowPygame, self).release_keyboard(*largs)
        if android:
            android.hide_keyboard()
        return True

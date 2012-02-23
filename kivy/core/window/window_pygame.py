'''
Window Pygame: windowing provider based on Pygame
'''

__all__ = ('WindowPygame', )

# fail early if possible
import pygame

from . import WindowBase
from kivy.core import CoreCriticalException
from os import environ
from os.path import exists, join
from kivy.config import Config
from kivy import kivy_home_dir
from kivy.base import ExceptionManager
from kivy.logger import Logger
from kivy.base import stopTouchApp, EventLoop
from kivy.clock import Clock
from kivy.utils import platform

try:
    android = None
    if platform() == 'android':
        import android
except ImportError:
    pass

# late binding
glReadPixels = GL_RGBA = GL_UNSIGNED_BYTE = None


class WindowPygame(WindowBase):

    def create_window(self):
        params = self.params

        # force display to show (available only for fullscreen)
        displayidx = Config.getint('graphics', 'display')
        if not 'SDL_VIDEO_FULLSCREEN_HEAD' in environ and displayidx != -1:
            environ['SDL_VIDEO_FULLSCREEN_HEAD'] = '%d' % displayidx

        # init some opengl, same as before.
        self.flags = pygame.HWSURFACE | pygame.OPENGL | \
                     pygame.DOUBLEBUF

        # right now, activate resizable window only on linux.
        # on window / macosx, the opengl context is lost, and we need to
        # reconstruct everything. Check #168 for a state of the work.
        if platform() == 'linux':
            self.flags |= pygame.RESIZABLE

        try:
            pygame.display.init()
        except pygame.error, e:
            raise CoreCriticalException(e.message)

        multisamples = Config.getint('graphics', 'multisamples')

        if multisamples > 0:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES,
                multisamples)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 1)
        pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)
        pygame.display.set_caption('kivy')

        if params['position'] == 'auto':
            self._pos = None
        elif params['position'] == 'custom':
            self._pos = params['left'], params['top']
        else:
            raise ValueError('position token in configuration accept only '
                             '"auto" or "custom"')

        self._fullscreenmode = params['fullscreen']
        if self._fullscreenmode == 'fake':
            Logger.debug('WinPygame: Set window to fake fullscreen mode')
            self.flags |= pygame.NOFRAME
            # if no position set, in fake mode, we always need to set the
            # position. so replace 0, 0.
            if self._pos is None:
                self._pos = (0, 0)
            environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        elif self._fullscreenmode:
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
            filename_icon = Config.get('kivy', 'window_icon')
            if filename_icon == '':
                logo_size = 512 if platform() == 'darwin' else 32
                filename_icon = join(kivy_home_dir, 'icon', 'kivy-icon-%d.png' %
                        logo_size)
            self.set_icon(filename_icon)
        except:
            Logger.exception('Window: cannot set icon')

        # init ourself size + setmode
        # before calling on_resize
        self._size = params['width'], params['height']

        # try to use mode with multisamples
        try:
            self._pygame_set_mode()
        except pygame.error, e:
            if multisamples:
                Logger.warning('WinPygame: Video: failed (multisamples=%d)' %
                               multisamples)
                Logger.warning('WinPygame: trying without antialiasing')
                pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
                pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
                multisamples = 0
                try:
                    self._pygame_set_mode()
                except pygame.error, e:
                    raise CoreCriticalException(e.message)
            else:
                raise CoreCriticalException(e.message)

        super(WindowPygame, self).create_window()

        # set mouse visibility
        pygame.mouse.set_visible(
            Config.getboolean('graphics', 'show_cursor'))

        # set rotation
        self.rotation = params['rotation']

        # if we are on android platform, automaticly create hooks
        if android:
            from kivy.support import install_android
            install_android()

    def close(self):
        pygame.display.quit()
        self.dispatch('on_close')

    def set_title(self, title):
        pygame.display.set_caption(title)

    def set_icon(self, filename):
        try:
            if not exists(filename):
                return False
            try:
                im = pygame.image.load(filename)
            except UnicodeEncodeError:
                im = pygame.image.load(filename.encode('utf8'))
            if im is None:
                raise Exception('Unable to load window icon (not found)')
            pygame.display.set_icon(im)
        except:
            Logger.exception('WinPygame: unable to set icon')

    def screenshot(self, *largs, **kwargs):
        global glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE
        filename = super(WindowPygame, self).screenshot(*largs, **kwargs)
        if filename is None:
            return None
        if glReadPixels is None:
            from kivy.core.gl import glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE
        width, height = self.size
        data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        data = str(buffer(data))
        surface = pygame.image.fromstring(data, self.size, 'RGBA', True)
        pygame.image.save(surface, filename)
        Logger.debug('Window: Screenshot saved at <%s>' % filename)
        return filename

    def on_keyboard(self, key, scancode=None, unicode=None, modifier=None):
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = platform() == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  #not sure what to do here
            return True
        super(WindowPygame, self).on_keyboard(key, scancode, unicode, modifier)

    def flip(self):
        pygame.display.flip()
        super(WindowPygame, self).flip()

    def toggle_fullscreen(self):
        if self.flags & pygame.FULLSCREEN:
            self.flags &= ~pygame.FULLSCREEN
        else:
            self.flags |= pygame.FULLSCREEN
        self._pygame_set_mode()

    def _mainloop(self):
        EventLoop.idle()

        for event in pygame.event.get():

            # kill application (SIG_TERM)
            if event.type == pygame.QUIT:
                EventLoop.quit = True
                self.close()

            # mouse move
            elif event.type == pygame.MOUSEMOTION:
                # don't dispatch motion if no button are pressed
                if event.buttons == (0, 0, 0):
                    continue
                x, y = event.pos
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
                eventname = 'on_mouse_down'
                if event.type == pygame.MOUSEBUTTONUP:
                    eventname = 'on_mouse_up'
                self.dispatch(eventname, x, y, btn, self.modifiers)

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
                # don't use trigger here, we want to delay the resize event
                cb = self._do_resize
                Clock.unschedule(cb)
                Clock.schedule_once(cb, .1)

            elif event.type == pygame.VIDEOEXPOSE:
                self.canvas.ask_update()

            # ignored event
            elif event.type == pygame.ACTIVEEVENT:
                pass

            '''
            # unhandled event !
            else:
                Logger.debug('WinPygame: Unhandled event %s' % str(event))
            '''

    def _do_resize(self, dt):
        Logger.debug('Window: Resize window to %s' % str(self._size))
        self._pygame_set_mode(self._size)
        self.dispatch('on_resize', *self._size)

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        self.dispatch('on_resize', *self.size)

        while not EventLoop.quit and EventLoop.status == 'started':
            try:
                self._mainloop()
                if not pygame.display.get_active():
                    pygame.time.wait(100)
            except BaseException, inst:
                # use exception manager first
                r = ExceptionManager.handle_exception(inst)
                if r == ExceptionManager.RAISE:
                    stopTouchApp()
                    raise
                else:
                    pass

        # force deletion of window
        pygame.display.quit()

    def _set_size(self, size):
        if super(WindowPygame, self)._set_size(size):
            self._pygame_set_mode()
            return True
    size = property(WindowBase._get_size, _set_size)

    #
    # Pygame wrapper
    #
    def _pygame_set_mode(self, size=None):
        if size is None:
            size = self.size
        if self._fullscreenmode == 'auto':
            pygame.display.set_mode((0, 0), self.flags)
            info = pygame.display.Info()
            self._size = (info.current_w, info.current_h)
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

    def request_keyboard(self, *largs):
        keyboard = super(WindowPygame, self).request_keyboard(*largs)
        if android:
            android.show_keyboard()
        return keyboard

    def release_keyboard(self, *largs):
        super(WindowPygame, self).release_keyboard(*largs)
        if android:
            android.hide_keyboard()
        return True

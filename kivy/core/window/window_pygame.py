'''
Window Pygame: windowing provider based on Pygame
'''

__all__ = ('WindowPygame', )

from . import WindowBase

import os
from time import sleep, time
from kivy.config import Config
from kivy.clock import Clock
from kivy.exceptions import ExceptionManager
from kivy.logger import Logger
from kivy.base import stopTouchApp, EventLoop

try:
    import pygame
except:
    Logger.warning('WinPygame: Pygame is not installed !')
    raise

class WindowPygame(WindowBase):
    def create_window(self, params):
        # force display to show (available only for fullscreen)
        displayidx = Config.getint('graphics', 'display')
        if not 'SDL_VIDEO_FULLSCREEN_HEAD' in os.environ and displayidx != -1:
            os.environ['SDL_VIDEO_FULLSCREEN_HEAD'] = '%d' % displayidx

        # init some opengl, same as before.
        self.flags = pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF

        pygame.display.init()

        multisamples = Config.getint('graphics', 'multisamples')

        if multisamples > 0:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, multisamples)
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
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        elif self._fullscreenmode:
            Logger.debug('WinPygame: Set window to fullscreen mode')
            self.flags |= pygame.FULLSCREEN

        elif self._pos is not None:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        # never stay with a None pos, application using w.center will be fired.
        self._pos = (0, 0)

        # prepare keyboard
        repeat_delay = int(Config.get('keyboard', 'repeat_delay'))
        repeat_rate = float(Config.get('keyboard', 'repeat_rate'))
        pygame.key.set_repeat(repeat_delay, int(1000. / repeat_rate))

        # set window icon before calling set_mode
        # XXX FIXME
        #icon = pygame.image.load(Config.get('graphics', 'window_icon'))
        #pygame.display.set_icon(icon)

        # init ourself size + setmode
        # before calling on_resize
        self._size = params['width'], params['height']
        self._vsync = params['vsync']
        self._fps = float(params['fps'])

        # ensure the default fps will be 60 if vsync is actived
        # and if user didn't set any maximum fps.
        if self._vsync and self._fps <= 0:
            self._fps = 60.

        # try to use mode with multisamples
        try:
            self._pygame_set_mode()
        except pygame.error:
            if multisamples:
                Logger.warning('WinPygame: Video: failed (multisamples=%d)' %
                               multisamples)
                Logger.warning('Video: trying without antialiasing')
                pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
                pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
                multisamples = 0
                self._pygame_set_mode()
            else:
                Logger.warning('WinPygame: Video setup failed :-(')
                raise

        if multisamples:
            # XXX FIXME
            from kivy.core.gl import glEnable, GL_MULTISAMPLE_ARB
            try:
                glEnable(GL_MULTISAMPLE_ARB)
            except Exception:
                pass

        super(WindowPygame, self).create_window(params)

        # set mouse visibility
        pygame.mouse.set_visible(
            Config.getboolean('graphics', 'show_cursor'))

        # set rotation
        self.rotation = params['rotation']

    def close(self):
        pygame.display.quit()

    def on_keyboard(self, key, scancode=None, unicode=None):
        if key == 27:
            stopTouchApp()
            self.close()  #not sure what to do here
            return True
        super(WindowPygame, self).on_keyboard(key, scancode, unicode)

    def flip(self):
        pygame.display.flip()
        super(WindowPygame, self).flip()

        # do software vsync if asked
        # FIXME: vsync is surely not 60 for everyone
        # this is not a real vsync. this must be done by driver...
        # but pygame can't do vsync on X11, and some people
        # use hack to make it work under darwin...
        fps = self._fps
        if fps > 0:
            s = 1 / fps - (time() - Clock.get_time())
            if s > 0:
                sleep(s)

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
                evloop.quit = True
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
                                       event.scancode, event.unicode):
                    continue
                self.dispatch('on_keyboard', event.key,
                                    event.scancode, event.unicode)

            # video resize
            elif event.type == pygame.VIDEORESIZE:
                pass

            # ignored event
            elif event.type in (pygame.ACTIVEEVENT, pygame.VIDEOEXPOSE):
                pass

            # unhandled event !
            else:
                Logger.debug('WinPygame: Unhandled event %s' % str(event))

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        self.dispatch('on_resize', *self.size)

        while not EventLoop.quit:
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

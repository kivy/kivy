'''
SDL Window: Windowing provider directly based on our own wrapped version of SDL
'''

__all__ = ('WindowSDL', )

from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.config import Config
import os
import sys

try:
    from kivy.core import sdl
except:
    Logger.warning('WindowSDL: SDL wrapper failed to import!')
    raise


L_SHIFT = 1
R_SHIFT = 2
L_CTRL = 64
R_CTRL = 128
L_ALT = 256
R_ALT = 512
L_META = 1024
R_META = 2048


class WindowSDL(WindowBase):
    def __init__(self, **kwargs):
        super(WindowSDL, self).__init__(**kwargs)
        self._mousedown = False

    def create_window(self):
        params = self.params

        # force display to show (available only for fullscreen)
        displayidx = Config.getint('graphics', 'display')
        if not 'SDL_VIDEO_FULLSCREEN_HEAD' in os.environ and displayidx != -1:
            os.environ['SDL_VIDEO_FULLSCREEN_HEAD'] = '%d' % displayidx

        if params['position'] == 'auto':
            self._pos = None
        elif params['position'] == 'custom':
            self._pos = params['left'], params['top']
        else:
            raise ValueError('position token in configuration accept only '
                             '"auto" or "custom"')

        use_fake = False
        use_fullscreen = False
        self._fullscreenmode = params['fullscreen']
        if self._fullscreenmode == 'fake':
            Logger.debug('WindowSDL: Set window to fake fullscreen mode')
            use_fake = True
            # if no position set, in fake mode, we always need to set the
            # position. so replace 0, 0.
            if self._pos is None:
                self._pos = (0, 0)
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        elif self._fullscreenmode:
            Logger.debug('WindowSDL: Set window to fullscreen mode')
            use_fullscreen = True

        elif self._pos is not None:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        # never stay with a None pos, application using w.center will be fired.
        self._pos = (0, 0)

        '''
        # prepare keyboard
        repeat_delay = int(Config.get('kivy', 'keyboard_repeat_delay'))
        repeat_rate = float(Config.get('kivy', 'keyboard_repeat_rate'))
        pygame.key.set_repeat(repeat_delay, int(1000. / repeat_rate))

        # set window icon before calling set_mode
        filename_icon = Config.get('kivy', 'window_icon')
        self.set_icon(filename_icon)
        '''

        # init ourself size + setmode
        # before calling on_resize
        self._size = params['width'], params['height']

        # setup !
        w, h = self._size
        sdl.setup_window(w, h, use_fake, use_fullscreen)

        super(WindowSDL, self).create_window()

        '''
        # set mouse visibility
        pygame.mouse.set_visible(
            Config.getboolean('graphics', 'show_cursor'))
        '''

        # set rotation
        self.rotation = params['rotation']

    def close(self):
        sdl.teardown_window()
        self.dispatch('on_close')

    def on_keyboard(self, key, scancode=None, unicode=None, modifier=None):
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = sys.platform == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  #not sure what to do here
            return True
        super(WindowSDL, self).on_keyboard(key, scancode, unicode, modifier)

    def flip(self):
        sdl.flip()
        super(WindowSDL, self).flip()

    def _mainloop(self):
        EventLoop.idle()

        while True:
            event = sdl.poll()
            if event is False:
                break
            if event is None:
                continue

            action, args = event[0], event[1:]
            if action == 'quit':
                EventLoop.quit = True
                self.close()
                break

            if action == 'mousemotion' and self._mousedown:
                x, y = args
                self.dispatch('on_mouse_move', x, y, self.modifiers)

            elif action in ('mousebuttondown', 'mousebuttonup'):
                x, y, button = args
                btn = 'left'
                if button == 3:
                    btn = 'right'
                elif button == 2:
                    btn = 'middle'
                eventname = 'on_mouse_down'
                if action == 'mousebuttonup':
                    eventname = 'on_mouse_up'
                self._mousedown = not self._mousedown
                self.dispatch(eventname, x, y, btn, self.modifiers)

            # video resize
            elif action == 'windowresized':
                self._size = args
                # don't use trigger here, we want to delay the resize event
                cb = self._do_resize
                Clock.unschedule(cb)
                Clock.schedule_once(cb, .1)

            elif action == 'windowresized':
                 self.canvas.ask_update()

            elif action in ('keydown', 'keyup'):
                mod, key, scancode, unicode = args
                self._update_modifiers(mod)
                if action == 'keyup':
                    self.dispatch('on_key_up', key, scancode)
                    continue

                # don't dispatch more key if down event is accepted
                if self.dispatch('on_key_down', key, scancode, unichr(unicode),
                                 self.modifiers):
                    continue
                self.dispatch('on_keyboard', key, scancode, unichr(unicode),
                              self.modifiers)

    def _do_resize(self, dt):
        Logger.debug('Window: Resize window to %s' % str(self._size))
        sdl.resize_window(*self._size)
        self.dispatch('on_resize', *self._size)

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        self.dispatch('on_resize', *self.size)

        while not EventLoop.quit and EventLoop.status == 'started':
            try:
                self._mainloop()
            except BaseException, inst:
                # use exception manager first
                r = ExceptionManager.handle_exception(inst)
                if r == ExceptionManager.RAISE:
                    stopTouchApp()
                    raise
                else:
                    pass

        # force deletion of window
        sdl.teardown_window()

    def _update_modifiers(self, mods=None):
        self._modifiers = []
        if mods & (L_SHIFT | R_SHIFT):
            self._modifiers.append('shift')
        if mods & (L_ALT | R_ALT):
            self._modifiers.append('alt')
        if mods & (L_CTRL | R_CTRL):
            self._modifiers.append('ctrl')
        if mods & (L_META | R_META):
            self._modifiers.append('meta')

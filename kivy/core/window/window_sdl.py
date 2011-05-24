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
    Logger.warning('WinPygame: SDL wrapper failed to import!')
    raise


class WindowSDL(WindowBase):

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
            Logger.debug('WinPygame: Set window to fake fullscreen mode')
            use_fake = True
            # if no position set, in fake mode, we always need to set the
            # position. so replace 0, 0.
            if self._pos is None:
                self._pos = (0, 0)
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos

        elif self._fullscreenmode:
            Logger.debug('WinPygame: Set window to fullscreen mode')
            use_fullscreen = True

        elif self._pos is not None:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % self._pos
            pass

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
        self._size = sdl.setup_window(w, h, use_fake, use_fullscreen)

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

    def set_title(self, title):
        sdl.set_window_title(title)

    def set_icon(self, filename):
        return

    def screenshot(self, *largs, **kwargs):
        return
        filename = super(WindowPygame, self).screenshot(*largs, **kwargs)
        if filename is None:
            return None
        from kivy.core.gl import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE
        width, height = self.size
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        data = str(buffer(data))
        surface = pygame.image.fromstring(data, self.size, 'RGB', True)
        pygame.image.save(surface, filename)
        Logger.debug('Window: Screenshot saved at <%s>' % filename)
        return filename

    def on_keyboard(self, key, scancode=None, unicode=None, modifier=None):
        return
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = sys.platform == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  #not sure what to do here
            return True
        super(WindowPygame, self).on_keyboard(key, scancode, unicode, modifier)

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

            if action == 'mousemotion':
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
                self._pygame_update_modifiers(mod)
                if action == 'keyup':
                    self.dispatch('on_key_up', key, scancode)
                    continue

                # don't dispatch more key if down event is accepted
                if self.dispatch('on_key_down', key,
                                 scancode, unicode,
                                 self.modifiers):
                    continue
                self.dispatch('on_keyboard', key,
                              scancode, unicode,
                              self.modifiers)

            elif action == 'textinput':
                self.dispatch('on_keyboard', None, None, args[0],
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
        sdl.resize_window(*self._size)
        self.dispatch('on_resize', *self._size)

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        self.dispatch('on_resize', *self.size)
        print 'dispatched on_resize, size is', self.size

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

    #
    # Pygame wrapper
    #
    def _pygame_update_modifiers(self, mods=None):
        return
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

    def on_keyboard(self, key, scancode=None, unicode=None, modifier=None):
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = sys.platform == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  #not sure what to do here
            return True
        super(WindowSDL, self).on_keyboard(key, scancode, unicode, modifier)

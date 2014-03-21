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
from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.clock import Clock
from kivy.input.provider import MotionEventProvider
from kivy.input.motionevent import MotionEvent
from collections import deque
from kivy.core.window._window_sdl2 import _WindowSDL2Storage

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

    def create_window(self):
        use_fake = self.fullscreen == 'fake'
        use_fullscreen = False
        if self.fullscreen in ('auto', True):
            use_fullscreen = self.fullscreen

        # never stay with a None pos, application using w.center will be fired.
        self._pos = (0, 0)

        # setup !
        w, h = self._size
        self._size = self._win.setup_window(w, h, use_fake, use_fullscreen)

        super(WindowSDL, self).create_window()

        # auto add input provider
        Logger.info('Window: auto add sdl input provider')
        from kivy.base import EventLoop
        SDL2MotionEventProvider.win = self
        EventLoop.add_input_provider(SDL2MotionEventProvider('sdl', ''))

    def close(self):
        self._win.teardown_window()
        self.dispatch('on_close')

    def set_title(self, title):
        self._win.set_window_title(title)

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

            elif action == 'windowrestored':
                self.canvas.ask_update()

            elif action == 'windowminimized':
                self.do_pause()

            elif action in ('keydown', 'keyup'):
                mod, key, scancode, str = args

                # XXX ios keyboard suck, when backspace is hit, the delete
                # keycode is sent. fix it.
                if key == 127:
                    key = 8

                self._pygame_update_modifiers(mod)
                if action == 'keyup':
                    self.dispatch('on_key_up', key, scancode)
                    continue

                # don't dispatch more key if down event is accepted
                if self.dispatch('on_key_down', key,
                                 scancode, str,
                                 self.modifiers):
                    continue
                self.dispatch('on_keyboard', key,
                              scancode, str,
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
        self._win.resize_window(*self._size)
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
    def _pygame_update_modifiers(self, mods=None):
        return

    def on_keyboard(self, key, scancode=None, str=None, modifier=None):
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = sys.platform == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  # not sure what to do here
            return True
        super(WindowSDL, self).on_keyboard(key, scancode, str, modifier)

    def request_keyboard(self, *largs):
        self._sdl_keyboard = super(WindowSDL, self).request_keyboard(*largs)
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


'''
SDL Window: Windowing provider directly based on our own wrapped version of SDL
'''

__all__ = ('WindowSDL', )

from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.clock import Clock
from kivy.config import Config
import sys

try:
    from kivy.core.window import sdl
except:
    Logger.warning('WinPygame: SDL wrapper failed to import!')
    raise


from kivy.input.provider import MotionEventProvider
from kivy.input.motionevent import MotionEvent
from collections import deque

# When we are generating documentation, Config doesn't exist
_exit_on_escape = True
if Config:
    _exit_on_escape = Config.getboolean('kivy', 'exit_on_escape')


class SDLMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.profile = ('pos', )
        self.sx, self.sy = args
        super(SDLMotionEvent, self).depack(args)


class SDLMotionEventProvider(MotionEventProvider):
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
                touchmap[fid] = me = SDLMotionEvent('sdl', fid, (x, y))
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

    def create_window(self):
        use_fake = True
        use_fullscreen = False

        # never stay with a None pos, application using w.center will be fired.
        self._pos = (0, 0)

        # setup !
        w, h = self._size
        self._size = sdl.setup_window(w, h, use_fake, use_fullscreen)

        super(WindowSDL, self).create_window()

        # auto add input provider
        Logger.info('Window: auto add sdl input provider')
        from kivy.base import EventLoop
        SDLMotionEventProvider.win = self
        EventLoop.add_input_provider(SDLMotionEventProvider('sdl', ''))

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

            elif action in ('fingermotion', 'fingerdown', 'fingerup'):
                # for finger, pass the raw event to SDL motion event provider
                SDLMotionEventProvider.q.appendleft(event)

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

            elif action == 'windowminimized':
                self.do_pause()

            elif action == 'windowrestored':
                pass

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
        sdl.resize_window(*self._size)
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
            event = sdl.poll()
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
        sdl.teardown_window()

    #
    # Pygame wrapper
    #
    def _pygame_update_modifiers(self, mods=None):
        return

    def on_keyboard(self, key, scancode=None, str=None, modifier=None):
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = sys.platform == 'darwin'
        if _exit_on_escape and (key == 27 or (is_osx and key in (113, 119) and
                                              modifier == 1024)):
            stopTouchApp()
            self.close()  # not sure what to do here
            return True
        super(WindowSDL, self).on_keyboard(key, scancode, str, modifier)

    def request_keyboard(self, *largs):
        self._sdl_keyboard = super(WindowSDL, self).request_keyboard(*largs)
        sdl.show_keyboard()
        Clock.schedule_interval(self._check_keyboard_shown, 1 / 5.)
        return self._sdl_keyboard

    def release_keyboard(self, *largs):
        super(WindowSDL, self).release_keyboard(*largs)
        sdl.hide_keyboard()
        self._sdl_keyboard = None
        return True

    def _check_keyboard_shown(self, dt):
        if self._sdl_keyboard is None:
            return False
        if not sdl.is_keyboard_shown():
            self._sdl_keyboard.release()


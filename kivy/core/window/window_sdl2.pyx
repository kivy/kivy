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

include "../../../kivy/lib/sdl2.pxi"

__all__ = ('WindowSDL2', )

import sys
from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.clock import Clock
from kivy.input.provider import MotionEventProvider
from kivy.input.motionevent import MotionEvent
from collections import deque


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

cdef class _WindowSDLStorage:
    cdef SDL_Window *win
    cdef SDL_GLContext ctx
    cdef SDL_Surface *surface
    cdef int win_flags

    def __cinit__(self):
        self.win = NULL
        self.ctx = NULL
        self.surface = NULL
        self.win_flags = 0

    def die(self):
        raise RuntimeError(<bytes> SDL_GetError())

    def setup_window(self, width, height, use_fake, use_fullscreen):
        self.win_flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
        if use_fake:
            self.win_flags |= SDL_WINDOW_BORDERLESS
        if use_fullscreen:
            self.win_flags |= SDL_WINDOW_FULLSCREEN

        if SDL_Init(SDL_INIT_VIDEO) < 0:
            self.die()

        '''
        # Set default orientation (force landscape for now)
        cdef bytes orientations
        orientations = <bytes>environ.get('KIVY_ORIENTATION',
                'LandscapeLeft LandscapeRight');
        SDL_SetHint(SDL_HINT_ORIENTATIONS, orientations);
        '''

        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 16)
        SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 1)
        SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_RETAINED_BACKING, 0)
        SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)


        self.win = SDL_CreateWindow(NULL, 0, 0, width, height, self.win_flags)
        if not self.win:
            self.die()

        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);

        self.ctx = SDL_GL_CreateContext(self.win)
        if not self.ctx:
            self.die()
        cdef SDL_DisplayMode mode
        SDL_GetWindowDisplayMode(self.win, &mode)
        return mode.w, mode.h

    def resize_window(self, w, h):
        cdef SDL_DisplayMode mode
        SDL_GetWindowDisplayMode(self.win, &mode)
        mode.w = w
        mode.h = h
        SDL_SetWindowDisplayMode(self.win, &mode)
        SDL_GetWindowDisplayMode(self.win, &mode)

    def set_window_title(self, str title):
        SDL_SetWindowTitle(self.win, <bytes>title.decode('utf-8'))

    def teardown_window(self):
        SDL_GL_DeleteContext(self.ctx)
        SDL_DestroyWindow(self.win)
        SDL_Quit()

    def show_keyboard(self):
        if not SDL_IsTextInputActive():
            SDL_StartTextInput()

    def hide_keyboard(self):
        if SDL_IsTextInputActive():
            SDL_StopTextInput()

    def is_keyboard_shown(self):
        return SDL_IsTextInputActive()

    def poll(self):
        cdef SDL_Event event

        if SDL_PollEvent(&event) == 0:
            return False

        action = None
        if event.type == SDL_QUIT:
            return ('quit', )
        elif event.type == SDL_MOUSEMOTION:
            x = event.motion.x
            y = event.motion.y
            return ('mousemotion', x, y)
        elif event.type == SDL_MOUSEBUTTONDOWN or event.type == SDL_MOUSEBUTTONUP:
            x = event.button.x
            y = event.button.y
            button = event.button.button
            action = 'mousebuttondown' if event.type == SDL_MOUSEBUTTONDOWN else 'mousebuttonup'
            return (action, x, y, button)
        elif event.type == SDL_FINGERMOTION:
            fid = event.tfinger.fingerId
            x = event.tfinger.x
            y = event.tfinger.y
            return ('fingermotion', fid, x, y)
        elif event.type == SDL_FINGERDOWN or event.type == SDL_FINGERUP:
            fid = event.tfinger.fingerId
            x = event.tfinger.x
            y = event.tfinger.y
            action = 'fingerdown' if event.type == SDL_FINGERDOWN else 'fingerup'
            return (action, fid, x, y)
        elif event.type == SDL_WINDOWEVENT:
            if event.window.event == SDL_WINDOWEVENT_EXPOSED:
                action = ('windowexposed', )
            elif event.window.event == SDL_WINDOWEVENT_RESIZED:
                action = ('windowresized', event.window.data1, event.window.data2)
            elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
                action = ('windowminimized', )
            elif event.window.event == SDL_WINDOWEVENT_RESTORED:
                action = ('windowrestored', )
            else:
                if __debug__:
                    print('receive unknown sdl window event', event.type)
                pass
            return action
        elif event.type == SDL_KEYDOWN or event.type == SDL_KEYUP:
            action = 'keydown' if event.type == SDL_KEYDOWN else 'keyup'
            mod = event.key.keysym.mod
            scancode = event.key.keysym.scancode
            #unicode = event.key.keysym.unicode
            key = event.key.keysym.sym
            return (action, mod, key, scancode, None)
        elif event.type == SDL_TEXTINPUT:
            s = event.text.text.decode('utf-8')
            return ('textinput', s)
        else:
            if __debug__:
                print('receive unknown sdl event', event.type)
            pass

    def flip(self):
        SDL_GL_SwapWindow(self.win)


class WindowSDL(WindowBase):

    def __init__(self, **kwargs):
        self._win = _WindowSDLStorage()
        super(WindowSDL, self).__init__()

    def create_window(self):
        use_fake = self.fullscreen == 'fake'
        use_fullscreen = self.fullscreen in ('auto', True)

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


'''
SFML Window: Windowing provider directly based on our own wrapped version of SFML
'''

__all__ = ('WindowSDL', )

from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.clock import Clock
import sys

try:
    import sfml as sf
except:
    Logger.warning('WinSFML: SFML module failed to load!')
    raise


from kivy.input.provider import MotionEventProvider
from kivy.input.motionevent import MotionEvent
from collections import deque

class SFMLMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.profile = ('pos', )
        self.sx, self.sy = args

        super(SFMLMotionEvent, self).depack(args)

class SFMLMotionEventProvider(MotionEventProvider):
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
                touchmap[fid] = me = SFMLMotionEvent('sdl', fid, (x, y))
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


class WindowSFML(WindowBase):

    def create_window(self):
        use_fake = True
        use_fullscreen = False

        # never stay with a None pos, application using w.center will be fired.
        self._pos = (0, 0)

        # setup !
        self._window = sf.RenderWindow(
            sf.VideoMode.get_desktop_mode(), 'SFML Window', sf.Style.DEFAULT,
            sf.ContextSettings(depth=16, stencil=1))
        self._size = tuple(self._window.size)

        super(WindowSFML, self).create_window()

        # auto add input provider
        Logger.info('Window: auto add sfml input provider')
        SFMLMotionEventProvider.win = self
        EventLoop.add_input_provider(SFMLMotionEventProvider('sfml', ''))

        self._window.display()

    def close(self):
        self._window.close()
        self.dispatch('on_close')

    def set_title(self, title):
        self._window.title = title

    def set_icon(self, filename):
        image = sf.Image.load_from_file(filename)
        self._window.icon = image.pixels

    def _mainloop(self):
        """ TODO:
                - implement touch events
                - implement minimize event
                - impolement restore event
        """
        EventLoop.idle()

        while True:
            try:
                event = self._window.events.next()
            except StopIteration:
                break

            if event == sf.CloseEvent:
                EventLoop.quit = True
                self.close()
                break
            elif event == sf.MouseMoveEvent:
                x, y = event.position
                self.dispatch('on_mouse_move', x, y, self.modifiers)

            elif event == sf.MouseButtonEvent:
                self._update_modifiers(event)
                x, y = event.position

                if event.button == 1:
                    btn = 'left'
                elif event.button == 2:
                    btn = 'middle'
                elif event.button == 3:
                    btn = 'right'

                if event.pressed:
                    name = 'on_mouse_down'
                elif event.released:
                    name = 'on_mouse_up'

                self.dispatch(name, x, y, btn, self.modifiers)

            elif event == sf.ResizeEvent:
                self._size = tuple(event.size)
                cb = self._do_resize
                Clock.unschedule(cb)
                Clock.schedule_once(cb, .1)
                self.canvas.ask_update()

            elif event == sf.KeyEvent:
                self._update_modifiers(event)
                key = event.code

                if event.released:
                    # ios passes key AND scancode
                    self.dispatch('on_key_up', key)
                    continue

                if self.dispatch('on_key_down', key, self.modifiers):
                    continue

                self.dispatch('on_keyboard', key, self.modifiers)

    def _update_modifiers(self, event):
        self._modifiers = []

        if event.alt:
            self._modifiers.append('alt')
        if event.control:
            self._modifiers.append('ctrl')
        if event.shift:
            self._modifiers.append('shift')
        if event.system:
            self._modifiers.append('meta')

    def _do_resize(self, dt):
        Logger.debug('Window: Resize window to %s' % str(self._size))
        self._window.size = self._size
        self.dispatch('on_resize', *self._size)

    def mainloop(self):
        # don't known why, but pygame required a resize event
        # for opengl, before mainloop... window reinit ?
        self.dispatch('on_resize', *self.size)
        #print 'dispatched on_resize, size is', self.size

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
        #self._window.close()

    def on_keyboard(self, key, modifier=None):
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = sys.platform == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  #not sure what to do here
            return True

        super(WindowSDL, self).on_keyboard(key=key, modifier=modifier)

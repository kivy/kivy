'''
Window X11
==========

Window implementation in top of X11
'''

__all__ = ('WindowX11', )


from kivy.core.window import WindowBase
from kivy.logger import Logger
from kivy.config import Config
from kivy.base import stopTouchApp, EventLoop, ExceptionManager
from kivy.utils import platform
from os import environ

cdef extern from "X11/Xutil.h":
    int KeyPress
    int KeyRelease
    int ButtonPress
    int ButtonRelease
    int MotionNotify

    int ControlMask
    int ShiftMask
    int Mod3Mask
    int Mod4Mask

    ctypedef struct XKeyEvent:
        unsigned int keycode
        unsigned int state

    ctypedef struct XMotionEvent:
        int x, y
        unsigned int state

    ctypedef struct XButtonEvent:
        int x, y
        unsigned int state
        unsigned int button

    ctypedef union XEvent:
        int type
        XKeyEvent xkey
        XMotionEvent xmotion
        XButtonEvent xbutton

cdef extern int x11_create_window(int width, int height, int x, int y, \
        int resizable, int fullscreen, int border, char *title)
cdef extern void x11_gl_swap()
cdef extern int x11_idle()
cdef extern int x11_get_width()
cdef extern int x11_get_height()

ctypedef int (*event_cb_t)(XEvent *event)
cdef extern void x11_set_event_callback(event_cb_t callback)
cdef extern long x11_keycode_to_keysym(unsigned int keycode, int shiftDown)

_window_object = None

cdef list get_modifiers_from_state(unsigned int state):
    ret = []
    if state & ShiftMask:
        ret.append('shift')
    elif state & ControlMask:
        ret.append('ctrl')
    elif state & Mod3Mask:
        ret.append('alt')
    elif state & Mod4Mask:
        ret.append('meta')
    return ret

cdef int event_callback(XEvent *event):
    if event.type == KeyPress or event.type == KeyRelease:
        modifiers = get_modifiers_from_state(event.xkey.state)
        scancode = event.xkey.keycode
        key = x11_keycode_to_keysym(event.xkey.keycode, 'shift' in modifiers)
        if key == -1:
            return 0
        try:
            codepoint = chr(key)
        except:
            codepoint = None
        if event.type == KeyRelease:
            _window_object.dispatch('on_key_up', key, scancode)
            return 0
        if _window_object.dispatch('on_key_down', key, scancode, codepoint, modifiers):
            return 0
        _window_object.dispatch('on_keyboard', key, scancode, codepoint, modifiers)

    elif event.type == MotionNotify:
        modifiers = get_modifiers_from_state(event.xmotion.state)
        _window_object.dispatch('on_mouse_move',
                event.xmotion.x, event.xmotion.y, modifiers)

    # mouse motion
    elif event.type == ButtonPress or event.type == ButtonRelease:
        btn = 'left'
        if event.xbutton.button == 3:
            btn = 'right'
        elif event.xbutton.button == 2:
            btn = 'middle'
        elif event.xbutton.button == 4:
            btn = 'scrolldown'
        elif event.xbutton.button == 5:
            btn = 'scrollup'
        modifiers = get_modifiers_from_state(event.xbutton.state)
        eventname = 'on_mouse_down'
        if event.type == ButtonRelease:
            eventname = 'on_mouse_up'
        _window_object.dispatch(eventname,
                event.xbutton.x, event.xbutton.y, btn, modifiers)

    else:
        pass

    return 0

x11_set_event_callback(event_callback)


class WindowX11(WindowBase):

    def create_window(self, *args):
        global _window_object
        _window_object = self
        # ensure the mouse is still not up after window creation, otherwise, we
        # have some weird bugs
        self.dispatch('on_mouse_up', 0, 0, 'all', [])

        resizable = Config.getint('graphics', 'resizable')
        multisamples = Config.getint('graphics', 'multisamples')
        pos = (0, 0)

        if self.position == 'auto':
            pos = (0, 0)
        elif self.position == 'custom':
            pos = self.left, self.top
        else:
            raise ValueError('position token in configuration accept only '
                             '"auto" or "custom"')

        fullscreen = False
        border = True
        size = list(self.system_size)
        if self.fullscreen == 'fake':
            fullscreen = True
            Logger.debug('WinX11: Set window to fake fullscreen mode')
            border = False
            pos = (0, 0)

        elif self.fullscreen == 'auto':
            size = [-1, -1]
            fullscreen = True

        elif self.fullscreen is True:
            Logger.debug('WinX11: Set window to fullscreen mode')
            fullscreen = True

        if 'KIVY_WINDOW_NO_BORDER' in environ:
            border = False

        if x11_create_window(size[0], size[1], pos[0], pos[1],
                resizable, fullscreen, border, <char *><bytes>self.title) < 0:
            Logger.critical('WinX11: Unable to create the window')
            return

        size[0] = x11_get_width()
        size[1] = x11_get_height()

        self._pos = (0, 0)
        self.system_size = size
        super(WindowX11, self).create_window()

    def mainloop(self):
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

    def _mainloop(self):
        EventLoop.idle()
        if x11_idle() == 0:
            EventLoop.quit = True

    def flip(self):
        x11_gl_swap()
        super(WindowX11, self).flip()

    def on_keyboard(self, key,
        scancode=None, codepoint=None, modifier=None, **kwargs):

        codepoint = codepoint or kwargs.get('unicode')
        # Quit if user presses ESC or the typical OSX shortcuts CMD+q or CMD+w
        # TODO If just CMD+w is pressed, only the window should be closed.
        is_osx = platform == 'darwin'
        if key == 27 or (is_osx and key in (113, 119) and modifier == 1024):
            stopTouchApp()
            self.close()  # not sure what to do here
            return True
        super(WindowX11, self).on_keyboard(key, scancode,
            codepoint=codepoint, modifier=modifier)


'''
Support of WM_PEN message (Window platform)
===========================================
'''

__all__ = ('WM_PenProvider', 'WM_Pen')

import os
from kivy.input.providers.wm_common import PEN_OR_TOUCH_SIGNATURE, \
        PEN_OR_TOUCH_MASK, GWL_WNDPROC, WM_MOUSEMOVE, WM_LBUTTONUP, \
        WM_LBUTTONDOWN, WM_TABLET_QUERYSYSTEMGESTURE, \
        QUERYSYSTEMGESTURE_WNDPROC, PEN_EVENT_TOUCH_MASK
from kivy.input.touch import Touch

class WM_Pen(Touch):
    '''Touch representing the WM_Pen event. Support pos profile'''
    def depack(self, args):
        self.sx, self.sy = args[0], args[1]
        super(WM_Pen, self).depack(args)

    def __str__(self):
        return '<WMPen id:%d uid:%d pos:%s device:%s>' % (self.id, self.uid, str(self.spos), self.device)

if 'KIVY_DOC' in os.environ:
    # documentation hack
    WM_PenProvider = None

else:
    from collections import deque
    from ctypes.wintypes import ULONG
    from ctypes import wintypes, Structure, windll, byref, c_int16, \
            c_int, c_long, WINFUNCTYPE
    from kivy.input.provider import TouchProvider
    from kivy.input.factory import TouchFactory

    WNDPROC = WINFUNCTYPE(c_long, c_int, c_int, c_int, c_int)

    class RECT(Structure):
        _fields_ = [
        ('left', ULONG),
        ('top', ULONG),
        ('right', ULONG),
        ('bottom', ULONG)]

        x = property(lambda self: self.left)
        y = property(lambda self: self.top)
        w = property(lambda self: self.right-self.left)
        h = property(lambda self: self.bottom-self.top)
    win_rect = RECT()


    class WM_PenProvider(TouchProvider):

        def _is_pen_message(self, msg):
            info = windll.user32.GetMessageExtraInfo()
            if (info & PEN_OR_TOUCH_MASK) == PEN_OR_TOUCH_SIGNATURE: # its a touch or a pen
                if not info & PEN_EVENT_TOUCH_MASK:
                    return True

        def _pen_handler(self, msg, wParam, lParam):
            if msg not in (WM_LBUTTONDOWN, WM_MOUSEMOVE, WM_LBUTTONUP):
                return

            windll.user32.GetClientRect(self.hwnd, byref(win_rect))
            x = c_int16(lParam & 0xffff).value / float(win_rect.w)
            y = c_int16(lParam >> 16).value / float(win_rect.h)
            y = abs(1.0 - y)

            if msg == WM_LBUTTONDOWN:
                self.pen_events.appendleft(('down', x, y))
                self.pen_status = True

            if msg == WM_MOUSEMOVE and self.pen_status:
                self.pen_events.appendleft(('move', x, y))

            if msg == WM_LBUTTONUP:
                self.pen_events.appendleft(('up', x, y))
                self.pen_status = False

        def _pen_wndProc( self, hwnd, msg, wParam, lParam ):
            if msg == WM_TABLET_QUERYSYSTEMGESTURE:
                return QUERYSYSTEMGESTURE_WNDPROC
            if self._is_pen_message(msg):
                self._pen_handler(msg, wParam, lParam)
                return 1
            else:
                return windll.user32.CallWindowProcW(self.old_windProc, hwnd, msg, wParam, lParam)

        def start(self):
            self.uid = 0
            self.pen = None
            self.pen_status = None
            self.pen_events = deque()

            self.hwnd = windll.user32.GetActiveWindow()

            # inject our own wndProc to handle messages before window manager does
            self.new_windProc = WNDPROC(self._pen_wndProc)
            self.old_windProc = windll.user32.SetWindowLongW(
                self.hwnd,
                GWL_WNDPROC,
                self.new_windProc
            )

        def update(self, dispatch_fn):
            while True:

                try:
                    type, x, y = self.pen_events.pop()
                except:
                    break

                if  type == 'down':
                    self.uid += 1
                    self.pen = WM_Pen(self.device, self.uid, [x, y])
                if  type == 'move':
                    self.pen.move([x, y])

                dispatch_fn(type, self.pen)

        def stop(self):
            self.pen = None
            windll.user32.SetWindowLongW(
                self.hwnd,
                GWL_WNDPROC,
                self.old_windProc
            )

    TouchFactory.register('wm_pen', WM_PenProvider)

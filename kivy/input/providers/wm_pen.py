'''
Support for WM_PEN messages (Windows platform)
==============================================
'''

__all__ = ('WM_PenProvider', 'WM_Pen')

import os
from kivy.input.providers.wm_common import *
from kivy.input.motionevent import MotionEvent


class WM_Pen(MotionEvent):
    '''MotionEvent representing the WM_Pen event. Supports the pos profile.'''

    def depack(self, args):
        self.is_touch = True
        self.sx, self.sy = args[0], args[1]
        super(WM_Pen, self).depack(args)

    def __str__(self):
        i, u, s, d = (self.id, self.uid, str(self.spos), self.device)
        return '<WMPen id:%d uid:%d pos:%s device:%s>' % (i, u, s, d)


if 'KIVY_DOC' in os.environ:
    # documentation hack
    WM_PenProvider = None

else:
    from collections import deque
    from ctypes import windll, byref, c_int16, c_int
    from kivy.input.provider import MotionEventProvider
    from kivy.input.factory import MotionEventFactory

    win_rect = RECT()

    class WM_PenProvider(MotionEventProvider):

        def _is_pen_message(self, msg):
            info = windll.user32.GetMessageExtraInfo()
            # It's a touch or a pen
            if (info & PEN_OR_TOUCH_MASK) == PEN_OR_TOUCH_SIGNATURE:
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
                self.pen_events.appendleft(('begin', x, y))
                self.pen_status = True

            if msg == WM_MOUSEMOVE and self.pen_status:
                self.pen_events.appendleft(('update', x, y))

            if msg == WM_LBUTTONUP:
                self.pen_events.appendleft(('end', x, y))
                self.pen_status = False

        def _pen_wndProc(self, hwnd, msg, wParam, lParam):
            if msg == WM_TABLET_QUERYSYSTEMGESTURE:
                return QUERYSYSTEMGESTURE_WNDPROC
            if self._is_pen_message(msg):
                self._pen_handler(msg, wParam, lParam)
                return 1
            else:
                return windll.user32.CallWindowProcW(self.old_windProc,
                                                     hwnd, msg, wParam, lParam)

        def start(self):
            self.uid = 0
            self.pen = None
            self.pen_status = None
            self.pen_events = deque()

            self.hwnd = windll.user32.GetActiveWindow()

            # inject our own wndProc to handle messages
            # before window manager does
            self.new_windProc = WNDPROC(self._pen_wndProc)
            self.old_windProc = SetWindowLong_WndProc_wrapper(
                self.hwnd, self.new_windProc)

        def update(self, dispatch_fn):
            while True:

                try:
                    etype, x, y = self.pen_events.pop()
                except:
                    break

                if etype == 'begin':
                    self.uid += 1
                    self.pen = WM_Pen(self.device, self.uid, [x, y])
                elif etype == 'update':
                    self.pen.move([x, y])
                elif etype == 'end':
                    self.pen.update_time_end()

                dispatch_fn(etype, self.pen)

        def stop(self):
            self.pen = None
            SetWindowLong_WndProc_wrapper(self.hwnd, self.old_windProc)

    MotionEventFactory.register('wm_pen', WM_PenProvider)

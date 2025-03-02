'''
Support for WM_POINTER messages (Windows platform)
==============================================
'''

__all__ = ('WM_PointerProvider', 'WM_Pointer')

import os
from kivy.input.providers.wm_common import *
from kivy.input.motionevent import MotionEvent
from ctypes import (c_uint32, c_int, c_uint64, c_int32)
from ctypes.wintypes import pointer, HWND
from win32api import LOWORD

GET_POINTERID_WPARAM = LOWORD
GetPointerPenInfo = windll.user32.GetPointerPenInfo

(PT_POINTER,
PT_TOUCH,
PT_PEN,
PT_MOUSE,
PT_TOUCHPAD)=map(c_int,range(1,6))

WM_POINTERUPDATE = 0x0245
WM_POINTERDOWN = 0x0246
WM_POINTERENTER = 0x0249
WM_POINTERLEAVE = 0x024A
WM_POINTERUP = 0x0247

class POINTER_INFO(Structure):
    _fields_ = [
        ('pointerType', c_int),
        ('pointerId', c_uint32),
        ('frameId', c_uint32),
        ('pointerFlags', c_uint32),
        ("sourceDevice", HANDLE),
        ("hwndTarget", HWND),
        ("ptPixelLocation", POINT),
        ("ptHimetricLocation", POINT),
        ("ptPixelLocationRaw", POINT),
        ("ptHimetricLocationRaw", POINT),
        ("dwTime", DWORD),
        ('historyCount', c_uint32),
        ('inputData', c_int32),
        ("dwKeyStates", DWORD),
        ('PerformanceCount', c_uint64),
        ('ButtonChangeType', c_int),
    
    ] 
    
class POINTER_PEN_INFO(Structure):
    _fields_ = [
        ('pointerInfo', POINTER_INFO),
        ('penFlags', c_int),
        ('penMask', c_int),
        ('pressure', c_uint32),    # 0 to 1024
        ('rotation', c_uint32),    # 0 to 359
        ('tiltX', c_int32),    # -90 to +90
        ('tiltY', c_int32),    # -90 to +90
    
    ]

class WM_Pointer(MotionEvent):
    '''MotionEvent representing the WM_Pointer event. Supports the pos profile.'''

    def depack(self, args):
        self.is_touch = True
        self.profile = ['pos', 'pressure']
        self.sx, self.sy, self.pressure = args[0], args[1], args[2]
        super(WM_Pointer, self).depack(args)

    def __str__(self):
        i, u, s, d = (self.id, self.uid, str(self.spos), self.device)
        return '<WMPointer id:%d uid:%d pos:%s device:%s pressure:%d>' % (i, u, s, d, self.pressure)
if 'KIVY_DOC' in os.environ:
    # documentation hack
    WM_PointerProvider = None

else:
    from collections import deque
    from ctypes import windll, byref, c_int16, c_int
    from kivy.input.provider import MotionEventProvider
    from kivy.input.factory import MotionEventFactory

    win_rect = RECT()

    class WM_PointerProvider(MotionEventProvider):

        # def __init__(self, device,args):
            # super(WM_PointerProvider, self).__init__(device, args)
            # windll.user32.EnableMouseInPointer(BOOL(True))    #If this works (Win8 minimum) we should only get WM_POINTER Events
            # if windll.user32.IsMouseInPointerEnabled() != 1:
                # raise Exception
    
        def _is_pen_message(self, msg):
            info = windll.user32.GetMessageExtraInfo()
            # It's a touch or a pen
            if (info & PEN_OR_TOUCH_MASK) == PEN_OR_TOUCH_SIGNATURE:
                if not info & PEN_EVENT_TOUCH_MASK:
                    return True

        def _pointer_handler(self, msg, wParam, lParam):
            if msg not in (WM_POINTERDOWN, WM_POINTERUP, WM_POINTERUPDATE):
                return

            windll.user32.GetClientRect(self.hwnd, byref(win_rect))
            print("Winrect: ")
            print(win_rect.w)
            print(win_rect.x)
            x = c_int16(lParam & 0xffff).value / float(win_rect.w)
            y = c_int16(lParam >> 16).value / float(win_rect.h)
            y = abs(1.0 - y)
            print("windowx: ",c_int16(lParam & 0xffff).value,"windowy: ", c_int16(lParam >> 16).value)
            print("windowpenx: ",x,"windowpeny: ", y)
            penstruct = POINTER_PEN_INFO()

            if msg == WM_POINTERDOWN:# or msg == WM_POINTERENTER:
                pointerID = GET_POINTERID_WPARAM(wParam)
                if GetPointerPenInfo(pointerID,byref(penstruct)) != 0:
                    
                    self.pointer_events.appendleft(('begin', x, y,penstruct.pressure, pointerID))
                    self.pointer_status = True

            if msg == WM_POINTERUPDATE and self.pointer_status:
                pointerID = GET_POINTERID_WPARAM(wParam)
                if GetPointerPenInfo(pointerID,byref(penstruct)) != 0:
                    self.pointer_events.appendleft(('update',x, y,penstruct.pressure, pointerID))

            if msg == WM_POINTERUP:# or msg == WM_POINTERLEAVE:
                pointerID = GET_POINTERID_WPARAM(wParam)
                if GetPointerPenInfo(pointerID,byref(penstruct)) != 0:
                    self.pointer_events.appendleft(('end', x, y,penstruct.pressure, pointerID))
                    self.pointer_status = False

        def _pointer_wndProc(self, hwnd, msg, wParam, lParam):
            #if msg == WM_TABLET_QUERYSYSTEMGESTURE:
            #    return QUERYSYSTEMGESTURE_WNDPROC
            #if self._is_pen_message(msg):
            if msg in (WM_POINTERDOWN, WM_POINTERUP, WM_POINTERUPDATE):
                self._pointer_handler(msg, wParam, lParam)
                return 1
            else:
                return windll.user32.CallWindowProcW(self.old_windProc,
                                                     hwnd, msg, wParam, lParam)

        def start(self):
            self.uid = 0
            self.pointer = None
            self.pointer_status = None
            self.pointer_events = deque()
            self.hwnd = windll.user32.GetActiveWindow()

            # inject our own wndProc to handle messages
            # before window manager does
            self.new_windProc = WNDPROC(self._pointer_wndProc)
            self.old_windProc = SetWindowLong_wrapper(
                self.hwnd, GWL_WNDPROC, self.new_windProc)

        def update(self, dispatch_fn):
            while True:

                try:
                    etype, x, y, pressure, self.uid = self.pointer_events.pop()
                    pressure = float(pressure / 1024.0)
                    #x = x + 1980 #Quick local fix
                    print("X: ",x,"Y: ",y)
                except:
                    break

                if etype == 'begin':
                    #self.uid += 1
                    self.pointer = WM_Pointer(self.device, self.uid, [x, y, pressure])
                elif etype == 'update':
                    self.pointer.move([x, y, pressure])
                elif etype == 'end':
                    if self.pointer:
                        self.pointer.update_time_end()

                dispatch_fn(etype, self.pointer)

        def stop(self):
            self.pointer = None
            SetWindowLong_wrapper(self.hwnd, GWL_WNDPROC, self.old_windProc)

    MotionEventFactory.register('wm_pointer', WM_PointerProvider)

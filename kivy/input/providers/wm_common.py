'''
Common definitions for a Windows provider
=========================================

This file provides common definitions for constants used by WM_Touch / WM_Pen.
'''
import os

WM_MOUSEFIRST = 512
WM_MOUSEMOVE = 512
WM_LBUTTONDOWN = 513
WM_LBUTTONUP = 514
WM_LBUTTONDBLCLK = 515
WM_RBUTTONDOWN = 516
WM_RBUTTONUP = 517
WM_RBUTTONDBLCLK = 518
WM_MBUTTONDOWN = 519
WM_MBUTTONUP = 520
WM_MBUTTONDBLCLK = 521
WM_MOUSEWHEEL = 522
WM_MOUSELAST = 522

WM_TOUCH = 576
TOUCHEVENTF_MOVE = 1
TOUCHEVENTF_DOWN = 2
TOUCHEVENTF_UP = 4

PEN_OR_TOUCH_SIGNATURE = 0xFF515700
PEN_OR_TOUCH_MASK = 0xFFFFFF00
PEN_EVENT_TOUCH_MASK = 0x80

SM_CYCAPTION = 4

WM_TABLET_QUERYSYSTEMGESTURE = 0x000002CC
TABLET_DISABLE_PRESSANDHOLD = 0x00000001
TABLET_DISABLE_PENTAPFEEDBACK = 0x00000008
TABLET_DISABLE_PENBARRELFEEDBACK = 0x00000010
TABLET_DISABLE_TOUCHUIFORCEON = 0x00000100
TABLET_DISABLE_TOUCHUIFORCEOFF = 0x00000200
TABLET_DISABLE_TOUCHSWITCH = 0x00008000
TABLET_DISABLE_FLICKS = 0x00010000
TABLET_ENABLE_FLICKSONCONTEXT = 0x00020000
TABLET_ENABLE_FLICKLEARNINGMODE = 0x00040000
TABLET_DISABLE_SMOOTHSCROLLING = 0x00080000
TABLET_DISABLE_FLICKFALLBACKKEYS = 0x00100000
GWL_WNDPROC = -4


QUERYSYSTEMGESTURE_WNDPROC = (
    TABLET_DISABLE_PRESSANDHOLD |
    TABLET_DISABLE_PENTAPFEEDBACK |
    TABLET_DISABLE_PENBARRELFEEDBACK |
    TABLET_DISABLE_SMOOTHSCROLLING |
    TABLET_DISABLE_FLICKFALLBACKKEYS |
    TABLET_DISABLE_TOUCHSWITCH |
    TABLET_DISABLE_FLICKS)

if 'KIVY_DOC' not in os.environ:
    from ctypes.wintypes import (ULONG, HANDLE, DWORD, LONG, UINT,
                                 WPARAM, LPARAM, BOOL, HWND, POINT,
                                 RECT as RECT_BASE)
    from ctypes import (windll, WINFUNCTYPE, POINTER,
                        c_int, c_longlong, c_void_p, Structure,
                        sizeof, byref, cast)

    class RECT(RECT_BASE):
        x = property(lambda self: self.left)
        y = property(lambda self: self.top)
        w = property(lambda self: self.right - self.left)
        h = property(lambda self: self.bottom - self.top)

    # check availability of RegisterTouchWindow
    if not hasattr(windll.user32, 'RegisterTouchWindow'):
        raise Exception('Unsupported Window version')

    LRESULT = LPARAM
    WNDPROC = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)

    class TOUCHINPUT(Structure):
        _fields_ = [
            ('x', LONG),
            ('y', LONG),
            ('pSource', HANDLE),
            ('id', DWORD),
            ('flags', DWORD),
            ('mask', DWORD),
            ('time', DWORD),
            ('extraInfo', POINTER(ULONG)),
            ('size_x', DWORD),
            ('size_y', DWORD)]

        def size(self):
            return (self.size_x, self.size_y)

        def screen_x(self):
            return self.x / 100.0

        def screen_y(self):
            return self.y / 100.0

        def _event_type(self):
            if self.flags & TOUCHEVENTF_MOVE:
                return 'update'
            if self.flags & TOUCHEVENTF_DOWN:
                return 'begin'
            if self.flags & TOUCHEVENTF_UP:
                return 'end'
        event_type = property(_event_type)

    def SetWindowLong_WndProc_wrapper_generator(func):
        def _closure(hWnd, wndProc):
            oldAddr = func(hWnd, GWL_WNDPROC, cast(wndProc, c_void_p).value)
            return cast(c_void_p(oldAddr), WNDPROC)

        return _closure

    try:
        LONG_PTR = c_longlong
        windll.user32.SetWindowLongPtrW.restype = LONG_PTR
        windll.user32.SetWindowLongPtrW.argtypes = [HWND, c_int, LONG_PTR]
        SetWindowLong_WndProc_wrapper = \
            SetWindowLong_WndProc_wrapper_generator(
                windll.user32.SetWindowLongPtrW)
    except AttributeError:
        windll.user32.SetWindowLongW.restype = LONG
        windll.user32.SetWindowLongW.argtypes = [HWND, c_int, LONG]
        SetWindowLong_WndProc_wrapper = \
            SetWindowLong_WndProc_wrapper_generator(
                windll.user32.SetWindowLongW)

    windll.user32.GetMessageExtraInfo.restype = LPARAM
    windll.user32.GetMessageExtraInfo.argtypes = []
    windll.user32.GetClientRect.restype = BOOL
    windll.user32.GetClientRect.argtypes = [HANDLE, POINTER(RECT_BASE)]
    windll.user32.GetWindowRect.restype = BOOL
    windll.user32.GetWindowRect.argtypes = [HANDLE, POINTER(RECT_BASE)]
    windll.user32.CallWindowProcW.restype = LRESULT
    windll.user32.CallWindowProcW.argtypes = [WNDPROC, HWND, UINT, WPARAM,
                                              LPARAM]
    windll.user32.GetActiveWindow.restype = HWND
    windll.user32.GetActiveWindow.argtypes = []
    windll.user32.RegisterTouchWindow.restype = BOOL
    windll.user32.RegisterTouchWindow.argtypes = [HWND, ULONG]
    windll.user32.UnregisterTouchWindow.restype = BOOL
    windll.user32.UnregisterTouchWindow.argtypes = [HWND]
    windll.user32.GetTouchInputInfo.restype = BOOL
    windll.user32.GetTouchInputInfo.argtypes = [HANDLE, UINT,
                                                POINTER(TOUCHINPUT), c_int]
    windll.user32.GetSystemMetrics.restype = c_int
    windll.user32.GetSystemMetrics.argtypes = [c_int]

    windll.user32.ClientToScreen.restype = BOOL
    windll.user32.ClientToScreen.argtypes = [HWND, POINTER(POINT)]

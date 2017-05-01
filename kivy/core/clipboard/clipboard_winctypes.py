'''
Clipboard windows: an implementation of the Clipboard using ctypes.
'''

__all__ = ('ClipboardWindows', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'win':
    raise SystemError('unsupported platform for Windows clipboard')

import ctypes
from ctypes import wintypes
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
msvcrt = ctypes.cdll.msvcrt
c_char_p = ctypes.c_char_p
c_wchar_p = ctypes.c_wchar_p


class ClipboardWindows(ClipboardBase):

    def get(self, mimetype='text/plain'):
        GetClipboardData = user32.GetClipboardData
        GetClipboardData.argtypes = [wintypes.UINT]
        GetClipboardData.restype = wintypes.HANDLE

        user32.OpenClipboard(user32.GetActiveWindow())
        # 1 is CF_TEXT
        pcontents = GetClipboardData(13)
        if not pcontents:
            return ''
        data = c_wchar_p(pcontents).value.encode(self._encoding)
        user32.CloseClipboard()
        return data

    def put(self, text, mimetype='text/plain'):
        text = text.decode(self._encoding)  # auto converted later
        text += u'\x00'

        SetClipboardData = user32.SetClipboardData
        SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        SetClipboardData.restype = wintypes.HANDLE

        GlobalAlloc = kernel32.GlobalAlloc
        GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        GlobalAlloc.restype = wintypes.HGLOBAL

        CF_UNICODETEXT = 13

        user32.OpenClipboard(user32.GetActiveWindow())
        user32.EmptyClipboard()
        hCd = GlobalAlloc(0, len(text) * ctypes.sizeof(ctypes.c_wchar))
        msvcrt.wcscpy_s(c_wchar_p(hCd), len(text), c_wchar_p(text))
        SetClipboardData(CF_UNICODETEXT, hCd)
        user32.CloseClipboard()

    def get_types(self):
        return ['text/plain']

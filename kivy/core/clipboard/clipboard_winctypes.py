'''
Clipboard windows: an implementation of the Clipboard using ctypes.
'''

__all__ = ('ClipboardWindows', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'win':
    raise SystemError('unsupported platform for Windows clipboard')

import ctypes
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
msvcrt = ctypes.cdll.msvcrt
c_char_p = ctypes.c_char_p
c_wchar_p = ctypes.c_wchar_p


class ClipboardWindows(ClipboardBase):

    def get(self, mimetype='text/plain'):
        user32.OpenClipboard(0)
        # 1 is CF_TEXT
        pcontents = user32.GetClipboardData(13)
        if not pcontents:
            return ''
        data = c_wchar_p(pcontents).value.encode(self._encoding)
        # ctypes.windll.kernel32.GlobalUnlock(pcontents)
        user32.CloseClipboard()
        return data

    def put(self, text, mimetype='text/plain'):
        GMEM_DDESHARE = 0x2000
        CF_UNICODETEXT = 13
        user32.OpenClipboard(None)
        user32.EmptyClipboard()
        hCd = kernel32.GlobalAlloc(GMEM_DDESHARE, len(text) + 2)
        pchData = kernel32.GlobalLock(hCd)
        msvcrt.wcscpy(c_wchar_p(pchData), text)
        kernel32.GlobalUnlock(hCd)
        user32.SetClipboardData(CF_UNICODETEXT, hCd)
        user32.CloseClipboard()

    def get_types(self):
        return ['text/plain']

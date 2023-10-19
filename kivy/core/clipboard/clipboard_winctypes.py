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
        # Standard Clipboard Format "1" is "CF_TEXT"
        pcontents = GetClipboardData(13)

        # if someone pastes a FILE, the content is None for SCF 13
        # and the clipboard is locked if not closed properly
        if not pcontents:
            user32.CloseClipboard()
            return ''
        data = c_wchar_p(pcontents).value.encode(self._encoding)
        user32.CloseClipboard()
        return data

    def put(self, text, mimetype='text/plain'):

        SetClipboardData = user32.SetClipboardData
        SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        SetClipboardData.restype = wintypes.HANDLE

        GlobalAlloc = kernel32.GlobalAlloc
        GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        GlobalAlloc.restype = wintypes.HGLOBAL

        user32.OpenClipboard(user32.GetActiveWindow())
        user32.EmptyClipboard()

        # this allocates memory for the string and returns a handle to it
        # allocates fixed memory, len + 2 is for the null character
        # no need to  call GlobalFree here as SetClipboardData will do for you
        # noqa: E501 see: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata#parameters
        GMEM_FIXED = 0x0000
        hCd = GlobalAlloc(GMEM_FIXED, len(text) + 2)

        # copy the string into the allocated memory
        msvcrt.wcscpy(c_wchar_p(hCd), text)

        # standard clipboard format for unicode text
        # noqa: E501 see https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats#constants
        CF_UNICODETEXT = 13
        # set the clipboard data, later used by GetClipboardData()
        SetClipboardData(CF_UNICODETEXT, hCd)
        user32.CloseClipboard()

    def get_types(self):
        return ['text/plain']

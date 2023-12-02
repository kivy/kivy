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

GlobalLock = kernel32.GlobalLock
GlobalLock.argtypes = [wintypes.HGLOBAL]
GlobalLock.restype = wintypes.LPVOID

GlobalUnlock = kernel32.GlobalUnlock
GlobalUnlock.argtypes = [wintypes.HGLOBAL]
GlobalUnlock.restype = wintypes.BOOL

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class ClipboardWindows(ClipboardBase):

    def _copy(self, data):
        self._ensure_clipboard()
        self.put(data, self._clip_mime_type)

    def get(self, mimetype='text/plain'):
        GetClipboardData = user32.GetClipboardData
        GetClipboardData.argtypes = [wintypes.UINT]
        GetClipboardData.restype = wintypes.HANDLE

        user32.OpenClipboard(user32.GetActiveWindow())

        # GetClipboardData returns a HANDLE to the clipboard data
        # which is a memory object containing the data
        # See: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboarddata  # noqa: E501
        pcontents = GetClipboardData(CF_UNICODETEXT)

        # if someone pastes a FILE, the content is None for SCF 13
        # and the clipboard is locked if not closed properly
        if not pcontents:
            user32.CloseClipboard()
            return ''

        # The handle returned by GetClipboardData is a memory object
        # and needs to be locked to get the actual pointer to the data
        pcontents_locked = GlobalLock(pcontents)
        data = c_wchar_p(pcontents_locked).value
        GlobalUnlock(pcontents)

        user32.CloseClipboard()
        return data

    def put(self, text, mimetype="text/plain"):
        SetClipboardData = user32.SetClipboardData
        SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        SetClipboardData.restype = wintypes.HANDLE

        GlobalAlloc = kernel32.GlobalAlloc
        GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        GlobalAlloc.restype = wintypes.HGLOBAL

        user32.OpenClipboard(user32.GetActiveWindow())
        user32.EmptyClipboard()

        # The wsclen function returns the number of
        # wide characters in a string (not including the null character)
        text_len = msvcrt.wcslen(text) + 1

        # According to the docs regarding SetClipboardDatam, if the hMem
        # parameter identifies a memory object, the object must have
        # been allocated using the GMEM_MOVEABLE flag.
        # See: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata  # noqa: E501
        # The size of the memory object is the number of wide characters in
        # the string plus one for the terminating null character
        hCd = GlobalAlloc(
            GMEM_MOVEABLE, ctypes.sizeof(ctypes.c_wchar) * text_len
        )

        # Since the memory object is allocated with GMEM_MOVEABLE, should be
        # locked to get the actual pointer to the data.
        hCd_locked = GlobalLock(hCd)
        ctypes.memmove(
            c_wchar_p(hCd_locked),
            c_wchar_p(text),
            ctypes.sizeof(ctypes.c_wchar) * text_len,
        )
        GlobalUnlock(hCd)

        # Finally, set the clipboard data (and then close the clipboard)
        SetClipboardData(CF_UNICODETEXT, hCd)
        user32.CloseClipboard()

    def get_types(self):
        return ['text/plain']

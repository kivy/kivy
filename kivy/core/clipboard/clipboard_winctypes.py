'''
Clipboard windows: an implementation of the Clipboard using ctypes.
'''

__all__ = ('ClipboardWindows', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'win':
    raise SystemError('unsupported platform for Windows clipboard')

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
msvcrt = ctypes.cdll.msvcrt
c_char_p = ctypes.c_char_p


class ClipboardWindows(ClipboardBase):

    def get(self, mimetype='text/plain'):
        user32.OpenClipboard(0)
        # 1 is CF_TEXT
        pcontents = user32.GetClipboardData(1)
        data = c_char_p(pcontents).value
        #ctypes.windll.kernel32.GlobalUnlock(pcontents)
        user32.CloseClipboard()
        return data

    def put(self, data, mimetype='text/plain'):
        GMEM_DDESHARE = 0x2000
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        try:
            # works on Python 2 (bytes() only takes one argument)
            hCd = kernel32.GlobalAlloc(
                GMEM_DDESHARE, len(bytes(text)) + 1)
        except TypeError:
            # works on Python 3 (bytes() requires an encoding)
            hCd = kernel32.GlobalAlloc(
                GMEM_DDESHARE, len(bytes(text, 'ascii')) + 1)
        pchData = kernel32.GlobalLock(hCd)
        try:
            # works on Python 2 (bytes() only takes one argument)
            msvcrt.strcpy(
                c_char_p(pchData), bytes(text))
        except TypeError:
            # works on Python 3 (bytes() requires an encoding)
            msvcrt.strcpy(
                c_char_p(pchData), bytes(text, 'ascii'))
        kernel32.GlobalUnlock(hCd)
        user32.SetClipboardData(1, hCd)
        user32.CloseClipboard()

    def get_types(self):
        return list('text/plain',)


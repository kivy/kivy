'''
Clipboard windows: an implementation of the Clipboard using ctypes.
'''

__all__ = ('ClipboardWindows', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'win':
    raise SystemError('unsupported platform for Windows clipboard')


class ClipboardWindows(ClipboardBase):

    def get(self, mimetype='text/plain'):
        ctypes.windll.user32.OpenClipboard(0)
        # 1 is CF_TEXT
        pcontents = ctypes.windll.user32.GetClipboardData(1)
        data = ctypes.c_char_p(pcontents).value
        #ctypes.windll.kernel32.GlobalUnlock(pcontents)
        ctypes.windll.user32.CloseClipboard()
        return data

    def put(self, data, mimetype='text/plain'):
        GMEM_DDESHARE = 0x2000
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        try:
            # works on Python 2 (bytes() only takes one argument)
            hCd = ctypes.windll.kernel32.GlobalAlloc(
                GMEM_DDESHARE, len(bytes(text)) + 1)
        except TypeError:
            # works on Python 3 (bytes() requires an encoding)
            hCd = ctypes.windll.kernel32.GlobalAlloc(
                GMEM_DDESHARE, len(bytes(text, 'ascii')) + 1)
        pchData = ctypes.windll.kernel32.GlobalLock(hCd)
        try:
            # works on Python 2 (bytes() only takes one argument)
            ctypes.cdll.msvcrt.strcpy(
                ctypes.c_char_p(pchData), bytes(text))
        except TypeError:
            # works on Python 3 (bytes() requires an encoding)
            ctypes.cdll.msvcrt.strcpy(
                ctypes.c_char_p(pchData), bytes(text, 'ascii'))
        ctypes.windll.kernel32.GlobalUnlock(hCd)
        ctypes.windll.user32.SetClipboardData(1, hCd)
        ctypes.windll.user32.CloseClipboard()

    def get_types(self):
        return list('text/plain',)


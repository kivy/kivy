'''
Clipboard SDL2: an implementation of the Clipboard using sdl2.
'''

__all__ = ('ClipboardSDL2', )

from kivy.utils import platform
from kivy.compat import PY2
from kivy.core.clipboard import ClipboardBase

if platform() not in ('win', 'linux', 'macosx', 'android', 'ios'):
    raise SystemError('unsupported platform for pygame clipboard')

try:
    from _clipboard_sdl2 import _get_text, _has_text, _set_text
except ImportError:
    raise SystemError('extension not copiled??')


class ClipboardSDL2(ClipboardBase):

    def paste(self):
        return _get_text() if _has_text() else ''

    def copy(self, data=''):
        if PY2:
            data = data.encode('utf-8')
        _set_text(data)

    def get_types(self):
        return 'text/plain'

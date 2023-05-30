'''
Clipboard SDL2: an implementation of the Clipboard using sdl2.
'''

__all__ = ('ClipboardSDL2', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform not in ('win', 'linux', 'macosx', 'android', 'ios'):
    raise SystemError('unsupported platform for sdl2 clipboard')

try:
    from kivy.core.clipboard._clipboard_sdl2 import (
        _get_text, _has_text, _set_text)
except ImportError:
    from kivy.core import handle_win_lib_import_error
    handle_win_lib_import_error(
        'Clipboard', 'sdl2', 'kivy.core.clipboard._clipboard_sdl2')
    raise


class ClipboardSDL2(ClipboardBase):

    def get(self, mimetype):
        return _get_text() if _has_text() else ''

    def _ensure_clipboard(self):
        super(ClipboardSDL2, self)._ensure_clipboard()
        self._encoding = 'utf8'

    def put(self, data=b'', mimetype='text/plain'):
        _set_text(data)

    def get_types(self):
        return ['text/plain']

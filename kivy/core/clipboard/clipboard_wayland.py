'''
Clipboard Wayland: An implementation of the Clipboard using wl-clipboard.
'''

__all__ = ('ClipboardWayland', )

from kivy.utils import platform

if platform != 'linux':
    raise SystemError('Unsupported platform for wayland-clipboard')

from shutil import which

if not which('wl-paste'):
    raise SystemError('wl-clipboard cannot be found')

from subprocess import check_output
from kivy.core.clipboard import ClipboardBase
from kivy.logger import Logger


def _io(cmd, encoding: str = None):
    encoding = encoding or 'utf-8'

    return check_output(
        cmd, encoding=encoding, timeout=1
    )


Logger.info(
    'wl-clipboard: Version: %s',
    _io(['wl-paste', '--version']).splitlines()[0][13:]
)


class ClipboardWayland(ClipboardBase):
    def get(self, mimetype: str = None):
        mimetype = mimetype or 'text/plain'

        return _io(
            ['wl-paste', '--type', mimetype]
        )[:-1]

    def _ensure_clipboard(self, encoding: str = None):
        super(ClipboardWayland, self)._ensure_clipboard()
        self._encoding = encoding or 'utf-8'

    def put(self, data: bytes = b'', mimetype: str = None):
        mimetype = mimetype or 'text/plain;charset=utf-8'
        mtype = mimetype.split(';charset=')

        return _io(
            ['wl-copy', data.decode(mtype[1]), '--type', mtype[0]],
            encoding=mtype[1]
        )

    def get_types(self):
        return [u'text/plain']

    def get_cutbuffer(self):
        pass

    def set_cutbuffer(self, data: bytes):
        pass

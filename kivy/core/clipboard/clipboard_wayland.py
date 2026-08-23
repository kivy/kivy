'''
Clipboard Wayland: An implementation of the Clipboard using wl-clipboard.
'''

__all__ = ('ClipboardWayland', )

from kivy.utils import platform

if platform != 'linux':
    raise SystemError('Unsupported platform for wayland-clipboard')

from shutil import which

wl_copy, wl_paste = which('wl-copy'), which('wl-paste')

if not any((wl_copy, wl_paste)):
    raise SystemError('wl-clipboard is not installed')


from subprocess import check_output
from re import search
from kivy.core.clipboard import ClipboardBase
from kivy.logger import Logger


def _io(cmd, encoding: str = None):
    encoding = encoding or 'utf-8'

    return check_output(
        cmd, encoding=encoding, timeout=1
    )


info = search(r"^([\w-]+)\s+([\d\.]+)", _io([wl_paste, '--version']))
Logger.info(f'{info.group(1)}: v{info.group(2)}')


class ClipboardWayland(ClipboardBase):
    def get(self, mimetype: str = None):
        mimetype = mimetype or 'text/plain'

        return _io(
            [wl_paste, '--type', mimetype]
        ).removesuffix('\n')

    def _ensure_clipboard(self, encoding: str = None):
        super(ClipboardWayland, self)._ensure_clipboard()
        self._encoding = encoding or 'utf-8'

    def put(self, data: bytes = b'', mimetype: str = None):
        mimetype = mimetype or 'text/plain;charset=utf-8'
        mtype = mimetype.split(';charset=')

        return _io(
            [wl_copy, data.decode(mtype[1]), '--type', mtype[0]],
            encoding=mtype[1]
        )

    def get_types(self):
        return [u'text/plain']

    def get_cutbuffer(self):
        pass

    def set_cutbuffer(self, data: bytes):
        pass

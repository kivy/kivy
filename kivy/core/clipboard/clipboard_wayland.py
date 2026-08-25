'''
Clipboard Wayland: an implementation of the Clipboard using wl-clipboard.
'''

__all__ = ('ClipboardWayland', )

from shutil import which
from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'linux':
    raise SystemError('unsupported platform for wayland clipboard')


def _wayland_session_available():
    import os
    # libwayland does not require WAYLAND_DISPLAY: it defaults to wayland-0,
    # and WAYLAND_SOCKET is an already-connected fd from the compositor.
    if os.environ.get('WAYLAND_SOCKET'):
        return True
    # WAYLAND_DISPLAY is a socket *name* (wayland-0), not a path, unless it
    # starts with / (absolute socket path, libwayland >= 1.15).
    display = os.environ.get('WAYLAND_DISPLAY') or 'wayland-0'
    if display.startswith('/'):
        socket_path = display
    else:
        runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
        if not runtime_dir:
            return False
        socket_path = os.path.join(runtime_dir, display)
    return os.path.exists(socket_path)


if not _wayland_session_available():
    raise SystemError('not running under Wayland')


wl_copy, wl_paste = which('wl-copy'), which('wl-paste')

if not (wl_copy and wl_paste):
    raise SystemError('wl-clipboard is not installed')


def _io(cmd, data=None):
    from subprocess import CalledProcessError, DEVNULL, check_output
    try:
        return check_output(cmd, input=data, stderr=DEVNULL)
    except CalledProcessError:
        return b''


class ClipboardWayland(ClipboardBase):
    def get(self, mimetype='text/plain'):
        return _io([wl_paste, '--no-newline'])

    def put(self, data, mimetype='text/plain'):
        _io([wl_copy], data)

    def get_cutbuffer(self):
        return _io([wl_paste, '--no-newline', '--primary']).decode('utf8')

    def set_cutbuffer(self, data):
        if not isinstance(data, bytes):
            data = data.encode('utf8')
        _io([wl_copy, '--primary'], data)

    def get_types(self):
        types = _io([wl_paste, '--list-types']).decode(
            'utf-8', 'ignore').splitlines()
        return [t for t in types if t] or [u'text/plain']

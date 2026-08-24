"""Clipboard tests that require a Wayland session and wl-clipboard.

Skipped unless ``wl-copy`` / ``wl-paste`` are on PATH and a compositor
socket is reachable (``WAYLAND_DISPLAY``, default ``wayland-0``, or
``WAYLAND_SOCKET``). Ubuntu CI starts headless Sway and runs this file
in a separate pytest invocation so the main Xvfb suite stays on X11.
"""

import os
import sys
from shutil import which

import pytest


def _wayland_session_available():
    if os.environ.get('WAYLAND_SOCKET'):
        return True
    display = os.environ.get('WAYLAND_DISPLAY') or 'wayland-0'
    if display.startswith('/'):
        socket_path = display
    else:
        runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
        if not runtime_dir:
            return False
        socket_path = os.path.join(runtime_dir, display)
    return os.path.exists(socket_path)


pytestmark = [
    pytest.mark.skipif(sys.platform != 'linux', reason='Linux only'),
    pytest.mark.skipif(
        not _wayland_session_available(),
        reason='no Wayland compositor socket'),
    pytest.mark.skipif(
        not (which('wl-copy') and which('wl-paste')),
        reason='wl-clipboard is not installed'),
]


def test_provider_is_wayland():
    from kivy.core.clipboard import Clipboard
    assert Clipboard.__class__.__name__ == 'ClipboardWayland'


def test_clipboard_paste():
    from kivy.core.clipboard import Clipboard
    Clipboard.paste()


def test_clipboard_copy_paste():
    from kivy.core.clipboard import Clipboard
    txt1 = u"Hello 1"
    Clipboard.copy(txt1)
    assert Clipboard.paste() == txt1


def test_clipboard_copy_paste_with_emoji():
    from kivy.core.clipboard import Clipboard
    test_emoji_str = 'kivy 😀 😁 🤣 😃 😄 😅 😆 😉 😊 😋 😎 😍 😘 😗'
    Clipboard.copy(test_emoji_str)
    assert Clipboard.paste() == test_emoji_str

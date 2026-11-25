'''
OS drag-out (drag export) helpers for :class:`~kivy.core.window.Window`.

Provides a general MIME/callback API plus a file convenience wrapper. Platform
backends live in ``drag_export_macos``, ``drag_export_win``, and
``drag_export_x11``.

.. versionadded:: 3.1.0
'''

__all__ = (
    'DragFileItem',
    'MIME_TEXT_PLAIN',
    'MIME_URI_LIST',
    'available',
    'begin_drag',
    'begin_drag_files',
    'encode_uri_list',
    'file_descriptor_w',
    'group_descriptor_w',
)

import struct
from collections import namedtuple
from pathlib import Path

from kivy import Logger

MIME_TEXT_PLAIN = 'text/plain'
MIME_URI_LIST = 'text/uri-list'

# FILEDESCRIPTORW / FILEGROUPDESCRIPTORW bit packing (Windows OLE). Pure helpers
# so unit tests can cover astral-character padding without pywin32.
FD_ATTRIBUTES = 0x00000004
FD_FILESIZE = 0x00000040
FD_PROGRESSUI = 0x00004000
FILE_ATTRIBUTE_DIRECTORY = 0x10

DragFileItem = namedtuple('DragFileItem', ('name', 'is_dir', 'provide'))
'''One file/folder offered for OS drag-out.

:param name: basename shown to the OS (and used as the drop destination name).
:param is_dir: True if this item is a directory tree.
:param provide: ``callable(dest_path)`` that materializes the item at
    ``dest_path`` (file write, or mkdir + recursive contents). Return ``None``
    on success, or an error string. Called lazily only when a drop lands.
'''


def encode_uri_list(paths):
    '''Encode absolute paths as a ``text/uri-list`` body (CRLF, trailing CRLF).'''
    lines = []
    for path in paths:
        if not path:
            continue
        p = Path(path)
        if not p.is_absolute():
            p = p.absolute()
        lines.append(p.as_uri())
    return ('\r\n'.join(lines) + ('\r\n' if lines else '')).encode('utf-8')


def file_descriptor_w(name, is_dir, size=0):
    '''Pack one ``FILEDESCRIPTORW`` record (592 bytes).

    ``name`` may include backslash-relative subpaths so Explorer builds a tree.
    Astral characters are encoded as UTF-16-LE surrogate pairs; padding uses the
    encoded byte length, not ``len(name)``.
    '''
    flags = FD_PROGRESSUI | FD_ATTRIBUTES | (
        0 if is_dir else (FD_FILESIZE if size else 0))
    attrs = FILE_ATTRIBUTE_DIRECTORY if is_dir else 0
    enc = name.replace('/', '\\').encode('utf-16-le')[:518]
    if len(enc) >= 2 and 0xD8 <= enc[-1] <= 0xDB:
        enc = enc[:-2]
    name_field = (enc + b'\0\0').ljust(520, b'\0')[:520]
    return (
        struct.pack('<L', flags)
        + b'\0' * 16
        + b'\0' * 16
        + struct.pack('<L', attrs)
        + b'\0' * 24
        + struct.pack('<LL', (size >> 32) & 0xFFFFFFFF, size & 0xFFFFFFFF)
        + name_field)


def group_descriptor_w(entries):
    '''Pack ``FILEGROUPDESCRIPTORW`` for ``[(rel_name, is_dir, size), ...]``.'''
    return struct.pack('<L', len(entries)) + b''.join(
        file_descriptor_w(n, d, s) for n, d, s in entries)


def _normalize_action(action):
    action = (action or 'copy').lower()
    if action not in ('copy', 'move', 'link'):
        raise ValueError('action must be copy, move, or link')
    return action


def _log(level, message):
    if level in ('warn', 'error', 'warning'):
        Logger.warning('DragExport: %s' % message)
    else:
        Logger.info('DragExport: %s' % message)


def _backend():
    '''Return the platform module, or None if unavailable.'''
    from kivy.utils import platform
    if platform == 'macosx':
        from kivy.core.window import drag_export_macos as backend
    elif platform == 'win':
        from kivy.core.window import drag_export_win as backend
    elif platform == 'linux':
        from kivy.core.window import drag_export_x11 as backend
    else:
        return None
    if not backend.available():
        return None
    return backend


def available():
    '''True when the current platform can start an OS drag-out session.'''
    return _backend() is not None


def begin_drag(mime_types, data_provider, action='copy', on_complete=None):
    '''Start an OS drag session offering ``mime_types``.

    :param mime_types: sequence of MIME type strings.
    :param data_provider: ``callable(mime_type) -> bytes | str | None`` invoked
        lazily when the drop target requests that type.
    :param action: ``'copy'``, ``'move'``, or ``'link'`` (v1 backends honor
        copy; others may fall back to copy).
    :param on_complete: optional ``callable(accepted: bool)``.
    :returns: True if a session was armed/started, False if unavailable.
    '''
    action = _normalize_action(action)
    mime_types = list(mime_types or ())
    if not mime_types or data_provider is None:
        return False
    backend = _backend()
    if backend is None:
        _log('warn', 'begin_drag unavailable on this platform/provider')
        return False
    try:
        return bool(backend.begin_drag(
            mime_types, data_provider, action=action, on_complete=on_complete,
            log=_log))
    except Exception as exc:
        _log('warn', 'begin_drag failed (%s: %s)' % (type(exc).__name__, exc))
        return False


def begin_drag_files(items, action='copy', on_complete=None):
    '''Start an OS drag session of files/folders (lazy materialization).

    :param items: sequence of :class:`DragFileItem` (or 3-tuples
        ``(name, is_dir, provide)``).
    :param action: see :func:`begin_drag`.
    :param on_complete: optional ``callable(accepted: bool)``.
    :returns: True if a session was armed/started, False if unavailable.
    '''
    action = _normalize_action(action)
    normalized = []
    for item in items or ():
        if isinstance(item, DragFileItem):
            normalized.append(item)
        else:
            name, is_dir, provide = item
            normalized.append(DragFileItem(name, bool(is_dir), provide))
    if not normalized:
        return False
    backend = _backend()
    if backend is None:
        _log('warn', 'begin_drag_files unavailable on this platform/provider')
        return False
    try:
        return bool(backend.begin_drag_files(
            normalized, action=action, on_complete=on_complete, log=_log))
    except Exception as exc:
        _log('warn', 'begin_drag_files failed (%s: %s)' % (
            type(exc).__name__, exc))
        return False

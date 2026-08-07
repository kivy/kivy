'''Unit tests for Window drag-export helpers (pure + dispatch).'''

import struct
import sys
from unittest.mock import patch

import pytest

from kivy.core.window.drag_export import (
    DragFileItem,
    MIME_URI_LIST,
    available,
    begin_drag,
    begin_drag_files,
    encode_uri_list,
    file_descriptor_w,
    group_descriptor_w,
)


class TestEncodeUriList:
    def test_empty(self):
        assert encode_uri_list([]) == b''

    def test_single_path(self):
        body = encode_uri_list(['/tmp/hello world.txt'])
        assert body.startswith(b'file://')
        assert b'hello%20world.txt' in body
        assert body.endswith(b'\r\n')

    def test_multiple_crlf(self):
        body = encode_uri_list(['/a', '/b']).decode('utf-8')
        assert body == 'file:///a\r\nfile:///b\r\n'


class TestFileDescriptorW:
    def test_record_size(self):
        rec = file_descriptor_w('readme.txt', False, 42)
        assert len(rec) == 592

    def test_directory_flag(self):
        rec = file_descriptor_w('folder', True, 0)
        attrs = struct.unpack_from('<L', rec, 36)[0]
        assert attrs & 0x10  # FILE_ATTRIBUTE_DIRECTORY

    def test_astral_name_padding(self):
        # emoji is one Python char but a UTF-16 surrogate pair (4 bytes).
        name = 'photo_\U0001f4f8.txt'
        rec = file_descriptor_w(name, False, 10)
        assert len(rec) == 592
        name_field = rec[72:592]
        assert len(name_field) == 520
        decoded = name_field.decode('utf-16-le').rstrip('\0')
        assert decoded.startswith('photo_')

    def test_group_count(self):
        group = group_descriptor_w([
            ('dir', True, 0),
            ('dir\\a.txt', False, 3),
        ])
        count = struct.unpack_from('<L', group, 0)[0]
        assert count == 2
        assert len(group) == 4 + 2 * 592


class TestDispatch:
    def test_begin_drag_empty_returns_false(self):
        assert begin_drag([], lambda m: None) is False
        assert begin_drag(['text/plain'], None) is False

    def test_begin_drag_files_empty_returns_false(self):
        assert begin_drag_files([]) is False

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError):
            begin_drag(['text/plain'], lambda m: b'x', action='nope')

    def test_available_is_bool(self):
        assert isinstance(available(), bool)

    def test_begin_drag_files_calls_backend(self):
        item = DragFileItem('a.txt', False, lambda p: None)
        with patch('kivy.core.window.drag_export._backend') as backend_factory:
            backend = backend_factory.return_value
            backend.begin_drag_files.return_value = True
            assert begin_drag_files([item]) is True
            backend.begin_drag_files.assert_called_once()
            args, kwargs = backend.begin_drag_files.call_args
            assert args[0][0].name == 'a.txt'

    def test_begin_drag_calls_backend(self):
        with patch('kivy.core.window.drag_export._backend') as backend_factory:
            backend = backend_factory.return_value
            backend.begin_drag.return_value = True
            assert begin_drag([MIME_URI_LIST], lambda m: b'') is True
            backend.begin_drag.assert_called_once()

    def test_backend_failure_is_fail_soft(self):
        item = DragFileItem('a.txt', False, lambda p: None)
        with patch('kivy.core.window.drag_export._backend') as backend_factory:
            backend = backend_factory.return_value
            backend.begin_drag_files.side_effect = RuntimeError('boom')
            assert begin_drag_files([item]) is False


@pytest.mark.skipif(sys.platform != 'darwin', reason='macOS-only protocol probe')
class TestMacOSProtocols:
    def test_available_true_with_pyobjus(self):
        from kivy.core.window import drag_export_macos as mac
        assert mac.available() is True

    def test_file_promise_delegate_registers(self):
        from pyobjus import autoclass, objc_str
        from pyobjus.dylib_manager import load_framework, INCLUDE
        from kivy.core.window import drag_export_macos as mac

        load_framework(INCLUDE.AppKit)
        load_framework(INCLUDE.Foundation)
        mac._ensure_protocols()

        def provide(path):
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write('hi')
            return None

        delegate = mac.FilePromiseDelegate('hello.txt', provide)
        provider = autoclass(
            'NSFilePromiseProvider'
        ).alloc().initWithFileType_delegate_(
            objc_str('public.data'), delegate)
        assert provider is not None
        name = delegate.filePromiseProvider_fileNameForType_(
            provider, objc_str('public.data'))
        # pyobjus may return NSString wrapper or str
        text = name if isinstance(name, str) else name.cString()
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        assert 'hello' in text

'''
Tests for the pure-Python parts of kivy.lib.gstplayer: the error text, the
YUV conversion, seek coalescing and finding the runtime. None of them need
GStreamer.
'''

import os

import pytest

from kivy.lib.gstplayer import _policy, _runtime
from kivy.lib.gstplayer._policy import BusError, SeekQueue, error_text


def err(kind='other', message='boom', debug=None, http=0, domain='stream',
        code=1, source='src'):
    return BusError(kind, domain, code, message, debug, http, source)


class TestErrorText:

    def test_nothing(self):
        assert error_text([]) is None

    def test_specific_beats_generic_state_change(self):
        errors = [err('state-change', 'state change failed'),
                  err('other', 'Resource not found.')]
        assert error_text(errors) == 'Resource not found.'

    def test_only_generic(self):
        assert error_text([err('state-change', 'state change failed')]) == \
            'state change failed'

    def test_missing_plugin_wins(self):
        errors = [err('other', 'No decoder available')]
        assert error_text(errors, ['H.265 decoder', 'H.265 decoder']) == \
            'missing GStreamer plugin: H.265 decoder'

    def test_http_status(self):
        assert error_text([err(message='Not Found', http=404)]) == \
            'Not Found (HTTP 404)'

    @pytest.mark.parametrize('kind', ['other', 'stream-failed'])
    def test_libsoup2_transport_code_not_shown_as_http(self, kind):
        # libsoup 2 (GStreamer 1.24's installer): 2 = name not resolved.
        text = error_text([err(kind, 'Could not resolve server name.',
                               http=2, source='souphttpsrc0')])
        assert text == 'Could not resolve server name.'

    def test_stream_failed_gets_debug_tail(self):
        debug = 'gstbasesrc.c(3187): loop ():\n/GstPlayBin3:p/src:\n' \
                'streaming stopped, reason error (-5)'
        text = error_text([err('stream-failed', 'Internal data stream error.',
                               debug)])
        assert text == ('Internal data stream error. (streaming stopped, '
                        'reason error (-5))')

    def test_http_source_failure_without_status(self):
        text = error_text([err('stream-failed', 'Internal data stream error.',
                               'streaming stopped, reason error (-5)',
                               source='souphttpsrc1')])
        assert text.startswith('Could not connect to the server')

    def test_tuples_accepted(self):
        assert error_text([('other', 'core', 1, 'x', None, 0, None)]) == 'x'


class TestColorimetry:

    @pytest.mark.parametrize('value,height,expected', [
        (None, 1080, ('bt709', False)),
        (None, 480, ('bt601', False)),
        ('bt709', 480, ('bt709', False)),
        ('bt601', 1080, ('bt601', False)),
        ('bt2020', 2160, ('bt2020', False)),
        ('sRGB', 720, ('bt709', True)),
        ('1:4:0:0', 720, ('bt601', True)),     # JPEG: full range BT.601
        ('2:3:5:1', 480, ('bt709', False)),
        ('nonsense', 1080, ('bt709', False)),
        ('1:x:0:0', 480, ('bt601', False)),
    ])
    def test_parse(self, value, height, expected):
        assert _policy.parse_colorimetry(value, height) == expected

    def test_bt709_limited_coefficients(self):
        (rv, gu, gv, bu), (yoff, yscale, uvscale) = \
            _policy.yuv_conversion('bt709', 1080)
        assert rv == pytest.approx(1.5748, abs=1e-4)
        assert gu == pytest.approx(0.1873, abs=1e-4)
        assert gv == pytest.approx(0.4681, abs=1e-4)
        assert bu == pytest.approx(1.8556, abs=1e-4)
        assert yoff == pytest.approx(16 / 255.)
        assert yscale == pytest.approx(255 / 219.)
        assert uvscale == pytest.approx(255 / 224.)

    def test_full_range(self):
        _, rng = _policy.yuv_conversion('1:4:0:0', 480)
        assert rng == (0.0, 1.0, 1.0)


class TestOrientation:

    # A texture flipped vertically, as the provider's are.
    FLIPPED = (0, 1, 1, 1, 1, 0, 0, 0)

    def test_identity_and_unknown(self):
        assert _policy.orientation_corners('rotate-0') is None
        assert _policy.orientation_corners(None) is None
        assert _policy.orientation_corners('sideways') is None

    @pytest.mark.parametrize('tag', [
        'rotate-90', 'rotate-180', 'rotate-270', 'flip-rotate-0',
        'flip-rotate-90', 'flip-rotate-180', 'flip-rotate-270'])
    def test_permutation(self, tag):
        corners = _policy.orientation_corners(tag)
        assert sorted(corners) == [0, 1, 2, 3]

    def test_rotate_90_clockwise(self):
        # The picture's top-left ends up top-right: output (BL, BR, TR, TL)
        # shows input (BR, TR, TL, BL).
        coords = (0, 0, 1, 0, 1, 1, 0, 1)
        assert _policy.reorient_tex_coords(
            coords, _policy.orientation_corners('rotate-90')) == \
            (1, 0, 1, 1, 0, 1, 0, 0)

    def test_four_quarter_turns_are_identity(self):
        c = self.FLIPPED
        for _ in range(4):
            c = _policy.reorient_tex_coords(
                c, _policy.orientation_corners('rotate-90'))
        assert c == self.FLIPPED

    def test_mirror_twice_is_identity(self):
        m = _policy.orientation_corners('flip-rotate-0')
        assert _policy.reorient_tex_coords(
            _policy.reorient_tex_coords(self.FLIPPED, m), m) == self.FLIPPED

    def test_flip_rotate_90_is_mirror_then_quarter_turn(self):
        mirror = _policy.orientation_corners('flip-rotate-0')
        turn = _policy.orientation_corners('rotate-90')
        both = _policy.reorient_tex_coords(
            _policy.reorient_tex_coords(self.FLIPPED, mirror), turn)
        assert both == _policy.reorient_tex_coords(
            self.FLIPPED, _policy.orientation_corners('flip-rotate-90'))

    @pytest.mark.parametrize('args,expected', [
        ((320, 180, 1, 1, None), (320, 180)),
        ((320, 180, 2, 1, None), (640, 180)),
        ((320, 180, 1, 2, None), (320, 360)),
        ((720, 480, 32, 27, None), (853, 480)),
        ((320, 180, 1, 1, 'rotate-90'), (180, 320)),
        ((320, 180, 2, 1, 'rotate-270'), (180, 640)),
        ((320, 180, 1, 1, 'flip-rotate-0'), (320, 180)),
        ((320, 180, 0, 0, None), (320, 180)),
    ])
    def test_display_size(self, args, expected):
        assert _policy.display_size(*args) == expected


class TestPathReplan:

    @pytest.mark.parametrize('caps,expected', [
        ('video/x-raw, format=(string)I420, width=(int)1920', True),
        ('video/x-raw,format=NV12', True),
        ('video/x-raw(memory:DMABuf), format=(string)DMA_DRM', False),
        ('video/x-raw(memory:GLMemory), format=(string)RGBA', False),
        ('video/x-raw(memory:D3D11Memory), format=(string)NV12', False),
        ('', False),
        (None, False),
    ])
    def test_cpu_frames(self, caps, expected):
        assert _policy.cpu_frames_cheaper_on_nv12(caps) is expected

    @pytest.mark.parametrize('decoder,expected', [
        ('avdec_h264', True), ('vp9dec', True), ('dav1ddec', True),
        ('vah264dec', False), ('vavp9dec', False), ('v4l2slh265dec', False),
        ('nvh264dec', False), ('d3d12h264dec', False), (None, True),
    ])
    def test_hardware_decoder_copied_to_system_memory_stays(self, decoder,
                                                           expected):
        caps = 'video/x-raw, format=(string)NV12, width=(int)3840'
        assert _policy.cpu_frames_cheaper_on_nv12(caps, decoder) is expected


class TestSeekQueue:

    def test_first_request_issued(self):
        q = SeekQueue()
        assert q.request((5.0, True), 0.0) == (5.0, True)
        assert q.pending == 5.0

    def test_not_ready_is_queued_until_done(self):
        q = SeekQueue()
        assert q.request((5.0, True), 0.0, ready=False) is None
        assert q.pending == 5.0
        assert q.done(0.1) == (5.0, True)
        assert q.done(0.2) is None
        assert q.pending is None

    def test_burst_keeps_one_in_flight_and_ends_on_last(self):
        q = SeekQueue()
        issued = []
        for i in range(50):
            t = q.request((float(i), True), i * 0.016)
            if t is not None:
                issued.append(t)
            if i % 10 == 9:   # a seek completes every 10 requests
                nxt = q.done(i * 0.016)
                if nxt is not None:
                    issued.append(nxt)
        while True:
            nxt = q.done(1.0)
            if nxt is None:
                break
            issued.append(nxt)
        assert len(issued) <= 7
        assert issued[-1] == (49.0, True)

    def test_duplicate_of_in_flight_dropped(self):
        q = SeekQueue()
        q.request((0.0, False), 0.0)
        assert q.request((0.0, True), 0.01) is None
        assert q.done(0.1) is None

    def test_stuck_seek_times_out(self):
        q = SeekQueue(timeout=1.0)
        q.request((1.0, True), 0.0)
        assert q.request((2.0, True), 0.5) is None
        assert q.request((3.0, True), 2.0) == (3.0, True)

    def test_failed(self):
        q = SeekQueue()
        q.request((1.0, True), 0.0)
        q.failed()
        assert q.request((2.0, True), 0.1) == (2.0, True)


class TestRuntime:

    def test_linux_system(self):
        rt = _runtime.find_runtime({}, 'linux')
        assert rt.directory is None and rt.source == 'system'

    def test_linux_root(self, tmp_path):
        lib = tmp_path / 'lib' / 'x86_64-linux-gnu'
        lib.mkdir(parents=True)
        (lib / _runtime.LINUX_CORE).write_bytes(b'')
        rt = _runtime.find_runtime({'KIVY_GSTREAMER_ROOT': str(tmp_path)},
                                   'linux')
        assert rt.directory == str(lib)

    def test_root_without_library(self, tmp_path):
        rt = _runtime.find_runtime({'KIVY_GSTREAMER_ROOT': str(tmp_path)},
                                   'linux')
        assert rt.directory == str(tmp_path)

    @pytest.mark.parametrize('dll', _runtime.WINDOWS_CORE)
    def test_windows_installer(self, tmp_path, dll, monkeypatch):
        monkeypatch.setattr(_runtime, '_from_wheel', lambda: None)
        (tmp_path / 'bin').mkdir()
        (tmp_path / 'bin' / dll).write_bytes(b'')
        env = {'GSTREAMER_1_0_ROOT_MSVC_X86_64': str(tmp_path)}
        rt = _runtime.find_runtime(env, 'win32')
        assert rt.directory == os.path.join(str(tmp_path), 'bin')
        assert rt.dll_dirs == [rt.directory]

    def test_windows_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_runtime, '_from_wheel', lambda: None)
        (tmp_path / 'gstreamer-1.0-0.dll').write_bytes(b'')
        rt = _runtime.find_runtime({'PATH': str(tmp_path)}, 'win32')
        assert rt.directory == str(tmp_path) and rt.source == 'PATH'

    def test_windows_nothing(self, monkeypatch):
        monkeypatch.setattr(_runtime, '_from_wheel', lambda: None)
        rt = _runtime.find_runtime({'PATH': ''}, 'win32')
        assert rt.directory is None and rt.source == 'not found'

    def test_registry_not_prepended_to_user_value(self):
        rt = _runtime.Runtime('d', 'wheel', {
            'GST_REGISTRY_1_0': 'wheel.bin',
            'GIO_EXTRA_MODULES': 'gio'}, [])
        out = _runtime.merged_environment(rt, {'GST_REGISTRY_1_0': 'mine'})
        assert 'GST_REGISTRY_1_0' not in out
        assert out['GIO_EXTRA_MODULES'] == 'gio'

    def test_registry_path_per_installation(self, tmp_path):
        a = _runtime.registry_path(str(tmp_path / 'a'))
        b = _runtime.registry_path(str(tmp_path / 'b'))
        assert a != b
        assert a == _runtime.registry_path(str(tmp_path / 'a'))
        assert os.path.basename(os.path.dirname(a)) == 'gstreamer'

    def test_wheel_variables_include_tls_modules(self):
        assert 'GIO_EXTRA_MODULES' in _runtime.WHEEL_VARIABLES

    @pytest.mark.parametrize('version', [(1, 28, 7, 0), (1, 28, 7)])
    def test_known_issue_1_28_7(self, version):
        # adaptivedemux2 aborts in libsoup when an HLS/DASH pipeline stops
        # (upstream work item 5296).
        text = _policy.runtime_known_issue(version)
        assert '1.28.9' in text and '5296' in text

    @pytest.mark.parametrize('version', [
        (1, 24, 12, 0), (1, 26, 2, 0), (1, 28, 6, 0), (1, 28, 8, 0),
        (1, 28, 9, 0), (1, 29, 2, 0)])
    def test_no_known_issue(self, version):
        assert _policy.runtime_known_issue(version) is None


class TestKivy2GstreamerDeps:
    '''Kivy 2's kivy_deps.gstreamer (GStreamer 1.18) is skipped on import:
    it would set GST_PLUGIN_PATH and put 1.18 plugins into a newer
    GStreamer found through the installer or KIVY_GSTREAMER_ROOT.'''

    def test_not_imported(self, tmp_path):
        import subprocess
        import sys
        import kivy

        deps = tmp_path / 'kivy_deps'
        for name, var in (('gstreamer', 'OLD_GST'), ('gstreamer_dev', None),
                          ('other', 'OTHER_DEP')):
            (deps / name).mkdir(parents=True)
            body = "import os\nos.environ['{}'] = '1'\n".format(var) \
                if var else "raise RuntimeError('imported')\n"
            (deps / name / '__init__.py').write_text(body)
        (deps / '__init__.py').write_text('')
        env = dict(os.environ)
        env['PYTHONPATH'] = os.pathsep.join(
            [str(tmp_path), os.path.dirname(os.path.dirname(kivy.__file__))])
        env.update(KIVY_NO_ARGS='1', KIVY_NO_FILELOG='1',
                   KIVY_HOME=str(tmp_path / 'home'))
        for var in ('OLD_GST', 'OTHER_DEP'):
            env.pop(var, None)
        out = subprocess.run(
            [sys.executable, '-c',
             "import os, kivy; print('RESULT', os.environ.get('OLD_GST'), "
             "os.environ.get('OTHER_DEP'))"],
            env=env, capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, out.stderr
        assert 'RESULT None 1' in out.stdout
        log = out.stdout + out.stderr
        assert 'Not importing "kivy_deps.gstreamer"' in log
        assert 'Not importing "kivy_deps.gstreamer_dev"' in log

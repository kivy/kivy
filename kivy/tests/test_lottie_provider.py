'''
Tests for kivy.core.lottie
===========================

The test file is split into three layers:

* **Plain unittest.TestCase** - pure-Python tests that need no GL context.
  Covers :class:`~kivy.core.lottie.LottieBase` state machine, eos modes,
  seek, and capability flags.

* **Null provider tests** - verify all no-op methods return the correct types.

* **ThorVG provider tests** - integration tests that load the real Lottie
  fixture and exercise each API tier.  Skipped when the Cython
  :mod:`kivy.lib.thorvg` binding is not compiled into the current Kivy
  build.
'''

import os
import unittest
from pathlib import Path
import pytest


# ---------------------------------------------------------------------------
# Fixture path
# ---------------------------------------------------------------------------

FIXTURE = str(Path(__file__).parent / 'test_lottie.json')


# ---------------------------------------------------------------------------
# Minimal concrete LottieBase subclass for state-machine tests
# ---------------------------------------------------------------------------

class _FakeLottie:
    '''Minimal in-process stand-in that mimics LottieBase without Kivy deps.

    We use this for pure-Python tests so that importing kivy is not required.
    Real integration tests import the actual providers below.
    '''


# ---------------------------------------------------------------------------
# Layer 1 - LottieBase state machine (requires Kivy but no GL)
# ---------------------------------------------------------------------------

class TestLottieBaseStateMachine(unittest.TestCase):
    '''Tests for LottieBase playback state machine.'''

    def _make_provider(self):
        from kivy.core.lottie import LottieBase

        class _Provider(LottieBase):
            def load(self):
                self._duration = 2.0
                self._total_frames = 60.0
                self._state = ''
                self.dispatch('on_load')

        p = _Provider()
        p._filename = 'dummy.json'
        p.load()
        return p

    def test_initial_state(self):
        from kivy.core.lottie import LottieBase
        p = LottieBase()
        self.assertEqual(p.state, '')
        self.assertIsNone(p.texture)
        self.assertEqual(p.position, 0.0)
        self.assertEqual(p.duration, 0.0)
        self.assertEqual(p.total_frames, 0.0)

    def test_capability_flags_default_false(self):
        from kivy.core.lottie import LottieBase
        self.assertFalse(LottieBase.SUPPORTS_SLOTS)
        self.assertFalse(LottieBase.SUPPORTS_QUALITY)

    def test_play_pause_stop(self):
        p = self._make_provider()
        p.play()
        self.assertEqual(p.state, 'playing')
        p.pause()
        self.assertEqual(p.state, 'paused')
        p.stop()
        self.assertEqual(p.state, '')
        self.assertEqual(p.position, 0.0)

    def test_play_idempotent(self):
        p = self._make_provider()
        p.play()
        event_before = p._clock_event
        p.play()
        self.assertIs(p._clock_event, event_before)

    def test_pause_only_when_playing(self):
        p = self._make_provider()
        p.pause()
        self.assertEqual(p.state, '')

    def test_seek_clamps(self):
        p = self._make_provider()
        p.seek(-0.5)
        self.assertEqual(p._position, 0.0)
        p.seek(1.5)
        self.assertAlmostEqual(p._position, p._duration)

    def test_seek_percent(self):
        p = self._make_provider()
        p.seek(0.5)
        self.assertAlmostEqual(p._position, 1.0)

    def test_eos_loop(self):
        p = self._make_provider()
        p.eos = 'loop'
        p._position = p._duration
        p._do_eos()
        self.assertEqual(p._position, 0.0)

    def test_eos_stop(self):
        p = self._make_provider()
        p.eos = 'stop'
        p.play()
        p._position = p._duration
        p._do_eos()
        self.assertEqual(p.state, '')

    def test_eos_pause(self):
        p = self._make_provider()
        p.eos = 'pause'
        p.play()
        p._position = p._duration
        p._do_eos()
        self.assertEqual(p.state, 'paused')
        self.assertAlmostEqual(p._position, p._duration)

    def test_eos_invalid(self):
        p = self._make_provider()
        with self.assertRaises(ValueError):
            p.eos = 'invalid'

    def test_refresh_no_crash_when_empty(self):
        from kivy.core.lottie import LottieBase
        p = LottieBase()
        p._refresh()

    def test_refresh_calls_render_frame(self):
        p = self._make_provider()
        frames_rendered = []
        original = p._render_frame
        p._render_frame = lambda f: frames_rendered.append(f)
        p._position = 1.0
        p._refresh()
        self.assertEqual(len(frames_rendered), 1)
        self.assertAlmostEqual(frames_rendered[0], 30.0)

    def test_filename_triggers_load(self):
        from kivy.core.lottie import LottieBase
        loaded = []

        class _P(LottieBase):
            def load(self):
                loaded.append(True)

        p = _P()
        p.filename = 'test.json'
        self.assertEqual(len(loaded), 1)

    def test_filename_none_clears(self):
        from kivy.core.lottie import LottieBase
        p = LottieBase()
        p._filename = 'test.json'
        p.filename = None
        self.assertIsNone(p._filename)

    def test_position_property_seeks(self):
        p = self._make_provider()
        frames = []
        p._render_frame = lambda f: frames.append(f)
        p.position = 1.0
        self.assertTrue(len(frames) > 0)


# ---------------------------------------------------------------------------
# Layer 2 - Null provider no-op contract
# ---------------------------------------------------------------------------

class TestLottieNullProvider(unittest.TestCase):
    '''Null provider must return correct types for all DOM API methods.'''

    def _make_null(self):
        from kivy.core.lottie.lottie_null import LottieNull
        p = LottieNull()
        return p

    def test_null_capability_flags(self):
        from kivy.core.lottie.lottie_null import LottieNull
        self.assertFalse(LottieNull.SUPPORTS_SLOTS)
        self.assertFalse(LottieNull.SUPPORTS_QUALITY)

    def test_null_markers_returns_list(self):
        p = self._make_null()
        result = p.markers
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_null_slots_returns_frozenset(self):
        p = self._make_null()
        result = p.slots
        self.assertIsInstance(result, frozenset)
        self.assertEqual(len(result), 0)

    def test_null_has_slot_false(self):
        p = self._make_null()
        self.assertFalse(p.has_slot('anything'))

    def test_null_apply_slot_returns_none(self):
        p = self._make_null()
        self.assertIsNone(p.apply_slot('{}'))

    def test_null_reset_slot_no_crash(self):
        p = self._make_null()
        p.reset_slot()
        p.reset_slot('sid')

    def test_null_set_color_returns_none(self):
        p = self._make_null()
        self.assertIsNone(p.set_color('sid', (1, 0, 0)))

    def test_null_set_opacity_returns_none(self):
        p = self._make_null()
        self.assertIsNone(p.set_opacity('sid', 0.5))

    def test_null_set_text_returns_none(self):
        p = self._make_null()
        self.assertIsNone(p.set_text('sid', 'hello'))

    def test_null_set_image_returns_none(self):
        p = self._make_null()
        self.assertIsNone(p.set_image('sid', '/path/to/img.png'))

    def test_null_set_quality_no_crash(self):
        p = self._make_null()
        p.set_quality(50)

    def test_null_play_segment_no_crash(self):
        p = self._make_null()
        p.play_segment(0, 30)

    def test_null_play_marker_no_crash(self):
        p = self._make_null()
        p.play_marker('highlight')

    def test_null_load_no_crash(self):
        '''load() should log a warning but not raise.'''
        from kivy.core.lottie.lottie_null import LottieNull
        p = LottieNull()
        p._filename = 'animation.json'
        p.load()


# ---------------------------------------------------------------------------
# Layer 3 - ThorVG provider integration
# ---------------------------------------------------------------------------

try:
    import kivy.lib.thorvg._thorvg  # noqa: F401
    _THORVG_AVAILABLE = True
except ImportError:
    _THORVG_AVAILABLE = False

_FIXTURE_EXISTS = os.path.exists(FIXTURE)
_SKIP_THORVG = not (_THORVG_AVAILABLE and _FIXTURE_EXISTS)
_SKIP_REASON = (
    'kivy.lib.thorvg not compiled into this Kivy build'
    if not _THORVG_AVAILABLE
    else f'fixture not found: {FIXTURE}'
)


@pytest.mark.skipif(_SKIP_THORVG, reason=_SKIP_REASON)
class TestLottieThorvgIntegration(unittest.TestCase):
    '''ThorVG provider integration tests: load, metadata, and all DOM API tiers.

    A single provider instance is shared across all tests in this class via
    ``setUpClass``/``tearDownClass`` so that exactly ONE ThorVG Engine and ONE
    GL texture is created for the entire class.  Creating multiple Engine
    instances in rapid succession within a single pytest session causes
    access violations due to GL context teardown between classes.
    '''

    @classmethod
    def setUpClass(cls):
        from kivy.core.lottie.lottie_thorvg import LottieThorvg
        cls.p = LottieThorvg(filename=FIXTURE, size=(64, 64))
        # Patch _render_frame so DOM API tests don't require a GL context.
        # Actual texture rendering is verified by test_uix_lottie.py which
        # uses GraphicUnitTest.
        cls.p._render_frame = lambda frame: None

    @classmethod
    def tearDownClass(cls):
        cls.p.unload()
        cls.p = None

    # ------------------------------------------------------------------
    # Load and metadata
    # ------------------------------------------------------------------

    def test_load_succeeds(self):
        self.assertGreater(self.p.duration, 0.0)
        self.assertGreater(self.p.total_frames, 0.0)

    def test_texture_initially_none(self):
        '''Texture is created lazily in _render_frame; None until first render.'''
        self.assertIsNone(self.p.texture)

    def test_capability_flags_true(self):
        from kivy.core.lottie.lottie_thorvg import LottieThorvg
        self.assertTrue(LottieThorvg.SUPPORTS_SLOTS)
        self.assertTrue(LottieThorvg.SUPPORTS_QUALITY)

    def test_slot_ids_populated(self):
        self.assertIn('fillColor', self.p.slots)

    def test_has_slot_true(self):
        self.assertTrue(self.p.has_slot('fillColor'))

    def test_has_slot_false(self):
        self.assertFalse(self.p.has_slot('nonexistent'))

    # ------------------------------------------------------------------
    # Tier 1: Segments and markers
    # ------------------------------------------------------------------

    def test_play_segment(self):
        self.p.play_segment(0.0, 15.0)

    def test_play_marker_success(self):
        self.p.play_marker('highlight')

    def test_play_marker_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.p.play_marker('does_not_exist')

    # ------------------------------------------------------------------
    # Tier 2: Slots
    # ------------------------------------------------------------------

    def test_set_color_returns_handle(self):
        handle = self.p.set_color('fillColor', (0.0, 1.0, 0.0))
        self.assertIsNotNone(handle)
        self.assertIsInstance(handle, int)
        self.assertGreater(handle, 0)

    def test_apply_slot_raw_json(self):
        import json
        slot_json = json.dumps({'fillColor': {'p': {'a': 0, 'k': [0.0, 0.0, 1.0]}}})
        handle = self.p.apply_slot(slot_json)
        self.assertIsNotNone(handle)
        self.assertGreater(handle, 0)

    def test_apply_slot_invalid_json_returns_none(self):
        handle = self.p.apply_slot('not valid json at all !!!')
        self.assertIsNone(handle)

    def test_reset_slot_by_id_no_crash(self):
        self.p.set_color('fillColor', (0.0, 1.0, 0.0))
        self.p.reset_slot('fillColor')

    def test_reset_all_slots_clears_active(self):
        self.p.set_color('fillColor', (0.0, 1.0, 0.0))
        self.p.reset_slot()
        self.assertEqual(self.p._active_slots, {})

    # ------------------------------------------------------------------
    # Rendering quality
    # ------------------------------------------------------------------

    def test_set_quality_no_crash(self):
        self.p.set_quality(0)
        self.p.set_quality(50)
        self.p.set_quality(100)

    # ------------------------------------------------------------------
    # Teardown / unload
    # ------------------------------------------------------------------

    def test_z_unload_clears_state(self):
        '''Run last (z_ prefix): verifies unload resets all internal state.'''
        self.p.unload()
        self.assertIsNone(self.p._tvg_anim)
        self.assertIsNone(self.p._tvg_canvas)
        self.assertEqual(self.p._slot_ids, frozenset())
        self.assertEqual(self.p._active_slots, {})


@pytest.mark.skipif(_SKIP_THORVG, reason=_SKIP_REASON)
class TestCollectSlotIds(unittest.TestCase):
    '''Unit tests for the _collect_slot_ids helper.'''

    def test_finds_sid_keys(self):
        from kivy.core.lottie.lottie_thorvg import _collect_slot_ids
        import json
        data = json.dumps({
            'layers': [{'shapes': [
                {'c': {'sid': 'fillColor'}, 'o': {'sid': 'opacity'}}
            ]}]
        }).encode()
        result = _collect_slot_ids(data)
        self.assertIn('fillColor', result)
        self.assertIn('opacity', result)

    def test_empty_json(self):
        from kivy.core.lottie.lottie_thorvg import _collect_slot_ids
        result = _collect_slot_ids(b'{}')
        self.assertEqual(result, frozenset())

    def test_invalid_json_returns_empty(self):
        from kivy.core.lottie.lottie_thorvg import _collect_slot_ids
        result = _collect_slot_ids(b'not json')
        self.assertEqual(result, frozenset())

    def test_returns_frozenset(self):
        from kivy.core.lottie.lottie_thorvg import _collect_slot_ids
        result = _collect_slot_ids(b'{}')
        self.assertIsInstance(result, frozenset)


if __name__ == '__main__':
    import sys
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    pytest.main([__file__, '-v'])

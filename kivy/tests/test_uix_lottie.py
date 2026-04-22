'''
LottieWidget tests
==================

The file is split into three layers:

* **Plain unittest.TestCase** — pure-Python helpers that need no GL context.

* **GraphicUnitTest (API layer)** — widget property and DOM delegation methods
  tested by injecting a mock :class:`~kivy.core.lottie.LottieBase` provider
  directly, without touching GL or actual Lottie files.

* **GraphicUnitTest (integration)** — full load cycle using a mock that
  simulates what ThorVG returns, so tests pass without requiring the
  :mod:`kivy.lib.thorvg` Cython binding to be compiled.
'''

import os
import unittest
from pathlib import Path

from kivy.tests.common import GraphicUnitTest, requires_graphics

# ---------------------------------------------------------------------------
# Fixture path
# ---------------------------------------------------------------------------

FIXTURE = str(Path(__file__).parent / 'test_lottie.json')


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------

def _make_mock_lottie_class(
    duration=2.0,
    total_frames=60.0,
    slot_ids=('fillColor',),
    markers=('highlight',),
    supports_slots=True,
):
    '''Return a LottieBase subclass that behaves like a real loaded provider
    but performs no ThorVG or file I/O.
    '''
    from kivy.core.lottie import LottieBase
    from kivy.graphics.texture import Texture

    _slot_ids = frozenset(slot_ids)
    _markers = list(markers)
    _supports_slots = supports_slots

    class _MockLottie(LottieBase):
        SUPPORTS_SLOTS = _supports_slots
        SUPPORTS_QUALITY = False

        def load(self):
            self._duration = duration
            self._total_frames = total_frames
            self._texture = Texture.create(size=(64, 64), colorfmt='rgba')
            self._slot_ids_internal = frozenset(_slot_ids)
            self._applied_colors = {}
            self.dispatch('on_load')

        def _render_frame(self, frame):
            self.dispatch('on_frame')

        @property
        def slots(self):
            return getattr(self, '_slot_ids_internal', frozenset())

        @property
        def markers(self):
            return list(_markers)

        def play_segment(self, begin, end):
            self._last_segment = (begin, end)
            self._refresh()

        def play_marker(self, name):
            if name not in _markers:
                raise ValueError(f'Marker {name!r} not found')
            self._last_marker = name
            self._refresh()

        def apply_slot(self, slot_data):
            import json
            try:
                parsed = json.loads(slot_data)
                key = next(iter(parsed))
                self._applied_colors[key] = slot_data
                return hash(slot_data) & 0x7FFFFFFF or 1
            except Exception:
                return None

        def reset_slot(self, slot_id=None):
            if slot_id is None:
                self._applied_colors.clear()
            else:
                self._applied_colors.pop(slot_id, None)

        def set_quality(self, value):
            self._last_quality = value

    return _MockLottie


# ---------------------------------------------------------------------------
# Helper: inject mock into kivy.core.lottie.Lottie
# ---------------------------------------------------------------------------

class _MockLottieInjection:
    '''Mixin that replaces kivy.core.lottie.Lottie with a mock class.'''

    def _inject_mock(self, **kwargs):
        import kivy.uix.lottie as _uix_lottie_mod
        self._MockClass = _make_mock_lottie_class(**kwargs)
        self._orig_get_lottie = _uix_lottie_mod._get_lottie

        def _patched_get_lottie():
            return self._MockClass

        _uix_lottie_mod._get_lottie = _patched_get_lottie
        self._uix_lottie_mod = _uix_lottie_mod

    def _restore_mock(self):
        self._uix_lottie_mod._get_lottie = self._orig_get_lottie


# ===========================================================================
# GraphicUnitTest — source load lifecycle
# ===========================================================================

@requires_graphics
class TestLottieWidgetLoad(_MockLottieInjection, GraphicUnitTest):
    '''Test that loading a source sets loaded/texture correctly.'''

    def setUp(self):
        super().setUp()
        self._inject_mock()

    def tearDown(self):
        self._restore_mock()
        super().tearDown()

    def test_initial_loaded_false(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget()
        self.assertFalse(w.loaded)
        self.assertIsNone(w.texture)

    def test_source_sets_loaded_true(self):
        from kivy.uix.lottie import LottieWidget
        load_events = []
        w = LottieWidget(size=(64, 64))
        w.bind(on_load=lambda *a: load_events.append(True))
        w.source = FIXTURE
        self.render(w)
        self.assertTrue(w.loaded)
        self.assertEqual(len(load_events), 1)

    def test_texture_not_none_after_load(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(w)
        self.assertIsNotNone(w.texture)

    def test_duration_populated_after_load(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(w)
        self.assertAlmostEqual(w.duration, 2.0)

    def test_total_frames_populated_after_load(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(w)
        self.assertAlmostEqual(w.total_frames, 60.0)

    def test_texture_size_matches_texture(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(w)
        if w.texture:
            self.assertEqual(w.texture_size, list(w.texture.size))

    def test_clear_source_resets(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(w)
        w.source = ''
        self.assertFalse(w.loaded)
        self.assertIsNone(w.texture)


# ===========================================================================
# GraphicUnitTest — playback control
# ===========================================================================

@requires_graphics
class TestLottieWidgetPlayback(_MockLottieInjection, GraphicUnitTest):
    '''Test play/pause/stop delegation to the underlying provider.'''

    def setUp(self):
        super().setUp()
        self._inject_mock()
        from kivy.uix.lottie import LottieWidget
        self.w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(self.w)

    def tearDown(self):
        self._restore_mock()
        super().tearDown()

    def test_play_sets_state(self):
        self.w.state = 'play'
        self.assertEqual(self.w.state, 'play')

    def test_pause_sets_state(self):
        self.w.state = 'play'
        self.w.state = 'pause'
        self.assertEqual(self.w.state, 'pause')

    def test_stop_resets_state(self):
        self.w.state = 'play'
        self.w.state = 'stop'
        self.assertEqual(self.w.state, 'stop')

    def test_state_play_before_load_starts_playback(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), state='play', source=FIXTURE)
        self.render(w)
        self.assertEqual(w.state, 'play')

    def test_state_play_at_construction(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(64, 64), state='play', source=FIXTURE)
        self.render(w)
        self.assertEqual(w.state, 'play')

    def test_progress_zero_before_seek(self):
        self.assertAlmostEqual(self.w.progress, 0.0, places=3)

    def test_progress_reflects_position(self):
        self.w.position = 1.0  # half of duration=2.0
        self.assertAlmostEqual(self.w.progress, 0.5, places=3)

    def test_set_progress_seeks(self):
        self.w.progress = 0.5
        self.assertAlmostEqual(self.w.position, 1.0, places=3)

    def test_progress_clamped(self):
        self.w.progress = 2.0
        self.assertLessEqual(self.w.progress, 1.0)
        self.w.progress = -1.0
        self.assertGreaterEqual(self.w.progress, 0.0)

    def test_progress_zero_when_no_duration(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget()
        self.assertAlmostEqual(w.progress, 0.0)


# ===========================================================================
# GraphicUnitTest — DOM manipulation delegation
# ===========================================================================

@requires_graphics
class TestLottieWidgetDom(_MockLottieInjection, GraphicUnitTest):
    '''Test that DOM methods delegate correctly to the provider.'''

    def setUp(self):
        super().setUp()
        self._inject_mock()
        from kivy.uix.lottie import LottieWidget
        self.w = LottieWidget(size=(64, 64), source=FIXTURE)
        self.render(self.w)

    def tearDown(self):
        self._restore_mock()
        super().tearDown()

    def test_slots_property(self):
        self.assertIn('fillColor', self.w.slots)

    def test_has_slot_true(self):
        self.assertTrue(self.w.has_slot('fillColor'))

    def test_has_slot_false(self):
        self.assertFalse(self.w.has_slot('nonexistent'))

    def test_markers_property(self):
        self.assertIn('highlight', self.w.markers)

    def test_set_color_returns_handle(self):
        handle = self.w.set_color('fillColor', (0.0, 1.0, 0.0))
        self.assertIsNotNone(handle)

    def test_set_opacity_returns_handle(self):
        handle = self.w.set_opacity('fillColor', 0.5)
        self.assertIsNotNone(handle)

    def test_set_text_returns_handle(self):
        handle = self.w.set_text('textSlot', 'hello')
        self.assertIsNotNone(handle)

    def test_play_segment_no_crash(self):
        self.w.play_segment(0.0, 15.0)
        self.assertEqual(self.w._lottie._last_segment, (0.0, 15.0))

    def test_play_marker_success(self):
        self.w.play_marker('highlight')
        self.assertEqual(self.w._lottie._last_marker, 'highlight')

    def test_play_marker_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.w.play_marker('bad_marker')

    def test_set_quality_no_crash(self):
        self.w.set_quality(75)
        self.assertEqual(self.w._lottie._last_quality, 75)

    def test_refresh_no_crash(self):
        self.w.refresh()

    def test_reset_slot_clears_color(self):
        self.w.set_color('fillColor', (1.0, 0.0, 0.0))
        self.w.reset_slot('fillColor')
        self.assertNotIn('fillColor', self.w._lottie._applied_colors)

    def test_reset_all_slots(self):
        self.w.set_color('fillColor', (1.0, 0.0, 0.0))
        self.w.reset_slot()
        self.assertEqual(self.w._lottie._applied_colors, {})

    def test_dom_before_load_returns_safe_values(self):
        '''DOM methods called before load should return safe defaults.'''
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget()
        self.assertEqual(w.slots, frozenset())
        self.assertFalse(w.has_slot('anything'))
        self.assertEqual(w.markers, [])
        self.assertIsNone(w.set_color('x', (1, 0, 0)))


# ===========================================================================
# GraphicUnitTest — fit_mode geometry
# ===========================================================================

@requires_graphics
class TestLottieWidgetFitMode(_MockLottieInjection, GraphicUnitTest):
    '''Test norm_image_size geometry for each fit_mode.'''

    def setUp(self):
        super().setUp()
        self._inject_mock()
        from kivy.uix.lottie import LottieWidget
        self.w = LottieWidget(
            size=(200, 100), size_hint=(None, None), source=FIXTURE
        )
        self.render(self.w)

    def tearDown(self):
        self._restore_mock()
        super().tearDown()

    def test_fill_uses_full_widget_size(self):
        self.w.fit_mode = 'fill'
        w, h = self.w.norm_image_size
        self.assertAlmostEqual(w, 200)
        self.assertAlmostEqual(h, 100)

    def test_contain_preserves_ratio(self):
        self.w.fit_mode = 'contain'
        w, h = self.w.norm_image_size
        # Texture is 64x64 (square); widget is 200x100 → h is the limit
        if w > 0 and h > 0:
            ratio = w / h
            self.assertAlmostEqual(ratio, 1.0, places=2)

    def test_norm_image_size_no_texture_returns_size(self):
        from kivy.uix.lottie import LottieWidget
        w = LottieWidget(size=(100, 100))
        result = w.norm_image_size
        self.assertEqual(result, [100, 100])


if __name__ == '__main__':
    import sys
    import pytest
    # Kivy replaces sys.stdout/stderr with ProcessingStream objects that lack
    # fileno(), which breaks pytest's capture mechanism.  Restore the real
    # streams before invoking pytest.
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    pytest.main([__file__, '-v'])

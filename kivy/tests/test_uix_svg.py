'''
SvgWidget and AsyncSvgWidget tests
===================================

Tests for :class:`~kivy.uix.svg.SvgWidget` and
:class:`~kivy.uix.svg.AsyncSvgWidget`.

The file is split into three layers:

* **Plain unittest.TestCase** — pure-Python helpers that need no GL context
  (_next_power_of_2, AsyncSvgWidget.is_uri).

* **GraphicUnitTest (element override API)** — widget property methods that
  operate on DictProperty without touching GL, but require a Kivy Widget
  context.  A mock provider is injected directly into the widget instance.

* **GraphicUnitTest (integration)** — full load-and-rasterize cycle.  A mock
  SvgProviderBase registered with SvgLoader replaces ThorVG so the tests run
  without thorvg-python installed.
'''

import unittest
from kivy.tests.common import GraphicUnitTest, requires_graphics

# ---------------------------------------------------------------------------
# In-memory SVG fixtures
# ---------------------------------------------------------------------------

SIMPLE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
    b'<rect width="64" height="64" fill="blue"/>'
    b'</svg>'
)

SIMPLE_SVG_WITH_IDS = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
    b'<rect id="bg" width="64" height="64" fill="blue"/>'
    b'<circle id="dot" cx="32" cy="32" r="10" fill="red"/>'
    b'</svg>'
)

# ---------------------------------------------------------------------------
# Mock provider factory
# ---------------------------------------------------------------------------

def _make_mock_provider_class(element_ids=None, doc_size=(64.0, 64.0)):
    '''Return a SvgProviderBase subclass that renders opaque black pixels.

    element_ids — list of id strings returned by get_element_ids().
    doc_size    — (w, h) float tuple returned by get_document_size().
    '''
    from kivy.core.svg import SvgProviderBase

    _ids = list(element_ids or [])
    _size = doc_size

    class _MockSvgProvider(SvgProviderBase):
        _provider_name = '_test_mock_svg'

        def load(self, source):
            return True

        def load_data(self, data, mimetype='svg'):
            return True

        def get_document_size(self):
            return _size

        def get_element_ids(self):
            return list(_ids)

        def render(self, width, height, current_color=None,
                   element_overrides=None):
            return b'\x00' * (width * height * 4)

    return _MockSvgProvider


# ---------------------------------------------------------------------------
# Helper mixin: isolate SvgLoader.providers across tests
# ---------------------------------------------------------------------------

class _SvgLoaderIsolation:
    '''setUp / tearDown helpers that save and restore SvgLoader state.

    Mix this in (before GraphicUnitTest) and call super().setUp/tearDown
    normally.
    '''

    def _inject_mock_provider(self):
        from kivy.core.svg import SvgLoader
        self._orig_providers = list(SvgLoader.providers)
        self._orig_by_name = dict(SvgLoader.providers_by_name)
        SvgLoader.providers[:] = [_make_mock_provider_class()]

    def _restore_providers(self):
        from kivy.core.svg import SvgLoader
        SvgLoader.providers[:] = self._orig_providers
        SvgLoader.providers_by_name.clear()
        SvgLoader.providers_by_name.update(self._orig_by_name)


# ===========================================================================
# Plain unittest tests (no GL)
# ===========================================================================

class TestNextPowerOf2(unittest.TestCase):
    '''Tests for the _next_power_of_2 helper in kivy.uix.svg.'''

    def setUp(self):
        from kivy.uix.svg import _next_power_of_2
        self._fn = _next_power_of_2

    def test_values(self):
        cases = [
            (1, 1),
            (2, 2),
            (3, 4),
            (4, 4),
            (5, 8),
            (255, 256),
            (256, 256),
            (257, 512),
            (512, 512),
            (1000, 1024),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(self._fn(n), expected)


class TestIsUri(unittest.TestCase):
    '''Tests for AsyncSvgWidget.is_uri static method.'''

    def setUp(self):
        from kivy.uix.svg import AsyncSvgWidget
        self._is_uri = AsyncSvgWidget.is_uri

    def test_http_url(self):
        self.assertTrue(self._is_uri('http://example.com/icon.svg'))

    def test_https_url(self):
        self.assertTrue(self._is_uri('https://example.com/icon.svg'))

    def test_https_url_mixed_case(self):
        self.assertTrue(self._is_uri('HTTPS://example.com/icon.svg'))

    def test_absolute_file_path(self):
        self.assertFalse(self._is_uri('/path/to/icon.svg'))

    def test_relative_file_path(self):
        self.assertFalse(self._is_uri('icon.svg'))

    def test_bytes_input(self):
        self.assertFalse(self._is_uri(b'<svg/>'))

    def test_none_input(self):
        self.assertFalse(self._is_uri(None))

    def test_ftp_protocol_not_uri(self):
        # Only http/https are accepted; ftp is not.
        self.assertFalse(self._is_uri('ftp://example.com/icon.svg'))

    def test_empty_string(self):
        self.assertFalse(self._is_uri(''))


# ===========================================================================
# GraphicUnitTest — element override API
# ===========================================================================

@requires_graphics
class TestElementOverrideApi(GraphicUnitTest):
    '''Tests for SvgWidget element visibility/opacity API.

    These tests operate entirely on the element_overrides DictProperty and
    do not trigger rasterization.  A mock provider is injected directly into
    the widget instance; _raster_size is kept at [0, 0] so that property
    change bindings do not fire _rasterize().
    '''

    def setUp(self):
        super().setUp()
        from kivy.uix.svg import SvgWidget

        MockProvider = _make_mock_provider_class(
            element_ids=['bg', 'dot', 'label'],
        )
        self._widget = SvgWidget(size=(64, 64), size_hint=(None, None))
        self._widget._svg_provider = MockProvider()
        self._widget.loaded = True
        # _raster_size stays at [0, 0] so _on_render_param is a no-op.

    def test_set_element_visible_false(self):
        self._widget.set_element_visible('bg', False)
        self.assertFalse(self._widget.is_element_visible('bg'))

    def test_set_element_visible_true(self):
        self._widget.set_element_visible('bg', False)
        self._widget.set_element_visible('bg', True)
        self.assertTrue(self._widget.is_element_visible('bg'))

    def test_hide_element(self):
        self._widget.hide_element('dot')
        self.assertFalse(self._widget.is_element_visible('dot'))

    def test_show_element(self):
        self._widget.hide_element('dot')
        self._widget.show_element('dot')
        self.assertTrue(self._widget.is_element_visible('dot'))

    def test_is_element_visible_default_true(self):
        # Elements with no override are considered visible.
        self.assertTrue(self._widget.is_element_visible('label'))

    def test_set_element_opacity(self):
        self._widget.set_element_opacity('bg', 0.5)
        self.assertAlmostEqual(self._widget.get_element_opacity('bg'), 0.5)

    def test_get_element_opacity_default_one(self):
        # Elements with no opacity override default to 1.0.
        self.assertAlmostEqual(self._widget.get_element_opacity('label'), 1.0)

    def test_reset_element_overrides_clears_all(self):
        self._widget.set_element_visible('bg', False)
        self._widget.set_element_opacity('dot', 0.3)
        self._widget.reset_element_overrides()
        self.assertEqual(self._widget.element_overrides, {})

    def test_multiple_overrides_independent(self):
        self._widget.hide_element('bg')
        self._widget.set_element_opacity('dot', 0.25)
        self.assertFalse(self._widget.is_element_visible('bg'))
        self.assertAlmostEqual(self._widget.get_element_opacity('dot'), 0.25)
        # label still has defaults
        self.assertTrue(self._widget.is_element_visible('label'))
        self.assertAlmostEqual(self._widget.get_element_opacity('label'), 1.0)


# ===========================================================================
# GraphicUnitTest — SvgWidget integration (mock provider)
# ===========================================================================

@requires_graphics
class TestSvgWidgetIntegration(_SvgLoaderIsolation, GraphicUnitTest):
    '''Integration tests for SvgWidget using a mock SVG provider.

    The mock provider is registered with SvgLoader so no real SVG
    rasterization (and no thorvg-python dependency) is needed.
    '''

    def setUp(self):
        self._inject_mock_provider()
        super().setUp()

    def tearDown(self):
        self._restore_providers()
        super().tearDown()

    def test_error_status_on_missing_source(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(
            source='definitely_does_not_exist.svg',
            size=(64, 64),
            size_hint=(None, None),
        )
        # Error is set synchronously in texture_update; no frame advance needed.
        self.assertEqual(w.status, 'error')
        self.assertFalse(w.loaded)

    def test_clear_on_none_source(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        # Setting source=None calls _clear_svg() synchronously — no render
        # needed to check the clear side-effects.
        w.source = None
        self.assertEqual(w.status, 'empty')
        self.assertIsNone(w.texture)
        self.assertFalse(w.loaded)

    def test_load_from_bytes_mipmap_false(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(
            source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None), mipmap=False
        )
        self.render(w, framecount=1)
        self.assertEqual(w.status, 'ready')
        self.assertTrue(w.loaded)

    def test_load_from_bytes_reaches_ready_status(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        self.assertEqual(w.status, 'ready')
        self.assertTrue(w.loaded)

    def test_texture_created_after_load(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        self.assertIsNotNone(w.texture)

    def test_viewbox_size_populated_after_load(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        self.assertEqual(w.viewbox_size, [64.0, 64.0])

    def test_on_load_event_fires(self):
        from kivy.uix.svg import SvgWidget
        fired = []
        w = SvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_load=lambda *a: fired.append(True))
        w.source = SIMPLE_SVG
        self.render(w, framecount=1)
        self.assertTrue(fired, 'on_load event was not dispatched')

    def test_on_error_event_fires_for_missing_file(self):
        from kivy.uix.svg import SvgWidget
        errors = []
        w = SvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_error=lambda inst, msg: errors.append(msg))
        w.source = 'nonexistent_file_for_testing.svg'
        self.assertTrue(errors, 'on_error event was not dispatched')

    def test_on_load_fires_only_once_on_first_load(self):
        from kivy.uix.svg import SvgWidget
        fired = []
        w = SvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_load=lambda *a: fired.append(True))
        w.source = SIMPLE_SVG
        self.render(w, framecount=1)
        self.assertEqual(len(fired), 1)

    def test_image_ratio_from_viewbox(self):
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        # Mock provider returns a 64x64 viewbox → ratio = 1.0
        self.assertAlmostEqual(w.image_ratio, 1.0, places=3)

    # -----------------------------------------------------------------------
    # Timing / event-ordering tests
    # -----------------------------------------------------------------------

    def test_on_load_fired_with_texture_already_set(self):
        # Regression: the deferred rasterize previously dispatched on_load
        # before assigning self.texture, so on_load handlers received a widget
        # whose texture was still None.  Verify the fix holds.
        from kivy.uix.svg import SvgWidget
        texture_at_on_load = []
        w = SvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_load=lambda inst: texture_at_on_load.append(inst.texture))
        w.source = SIMPLE_SVG
        self.render(w, framecount=1)
        self.assertTrue(texture_at_on_load, 'on_load was never dispatched')
        self.assertIsNotNone(
            texture_at_on_load[0],
            'texture was None when on_load fired',
        )

    def test_size_set_after_source_renders_at_final_size(self):
        # The deferred rasterize exists so KV can apply size bindings before
        # the first render fires.  Verify the texture reflects the size that
        # was set *after* source, not the Widget default (100 x 100).
        from kivy.uix.svg import SvgWidget, _next_power_of_2
        w = SvgWidget(source=SIMPLE_SVG, size_hint=(None, None))  # size not set yet
        w.size = (200, 200)  # applied "by KV" after source
        self.render(w, framecount=1)
        self.assertEqual(w.status, 'ready')
        # Expected bucket: _next_power_of_2(200) = 256
        expected = _next_power_of_2(200)
        tw, th = w.texture.size
        self.assertEqual(tw, expected,
                         f'texture width {tw} does not match expected {expected}')

    def test_source_change_cancels_pending_deferred_rasterize(self):
        # Changing source while a deferred rasterize is still pending must
        # cancel it and schedule a fresh one so only one rasterize runs.
        from kivy.uix.svg import SvgWidget
        render_calls = []
        w = SvgWidget(size=(64, 64), size_hint=(None, None))

        original_rasterize = w._rasterize

        def counting_rasterize(ww, hh):
            render_calls.append((ww, hh))
            original_rasterize(ww, hh)

        w._rasterize = counting_rasterize

        # Set source twice in the same clock tick (before the deferred
        # rasterize from the first set has a chance to fire).
        w.source = SIMPLE_SVG
        w.source = SIMPLE_SVG   # same bytes — simulates a rapid source swap

        self.render(w, framecount=1)
        # Exactly one rasterize should have run despite two source changes.
        self.assertEqual(len(render_calls), 1,
                         f'Expected 1 rasterize call, got {len(render_calls)}')

    def test_texture_size_matches_texture_dimensions(self):
        # texture_size is set via on_texture when self.texture is assigned.
        # Verify it reflects the actual texture pixel dimensions.
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        self.assertEqual(w.texture_size, list(w.texture.size))

    def test_reload_resets_state_and_reloads(self):
        # Mirrors test_reload_asyncimage from test_uix_asyncimage.py.
        # After reload(): loaded resets to False, then returns to True once
        # the deferred rasterize fires, and on_load fires a second time.
        from kivy.uix.svg import SvgWidget
        load_events = []
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        w.bind(on_load=lambda *a: load_events.append(True))
        self.render(w, framecount=1)
        self.assertEqual(len(load_events), 1)
        self.assertTrue(w.loaded)

        w.reload()
        self.assertFalse(w.loaded, 'reload() should reset loaded to False')
        self.render(w, framecount=1)
        self.assertTrue(w.loaded, 'loaded should be True after reload completes')
        self.assertEqual(len(load_events), 2, 'on_load should fire again after reload')

    def test_reload_updates_texture(self):
        # Verify that reload() produces a fresh texture object, not the same one.
        from kivy.uix.svg import SvgWidget
        w = SvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        first_texture = w.texture
        w.reload()
        self.render(w, framecount=1)
        # A new Texture instance should have been created.
        self.assertIsNotNone(w.texture)
        self.assertIsNot(w.texture, first_texture)

    def test_size_change_before_first_rasterize_does_not_double_rasterize(self):
        # _check_rerender guards against scheduling a second deferred
        # rasterize when texture_update already queued one.  Changing size
        # while the first deferred rasterize is still pending should not add
        # a second scheduled call.
        from kivy.uix.svg import SvgWidget
        render_calls = []
        w = SvgWidget(size=(64, 64), size_hint=(None, None))

        original_rasterize = w._rasterize

        def counting_rasterize(ww, hh):
            render_calls.append((ww, hh))
            original_rasterize(ww, hh)

        w._rasterize = counting_rasterize

        w.source = SIMPLE_SVG          # schedules deferred rasterize
        w.size = (128, 128)            # _check_rerender fires; guard prevents duplicate

        self.render(w, framecount=1)
        self.assertEqual(len(render_calls), 1,
                         f'Expected 1 rasterize call, got {len(render_calls)}')


# ===========================================================================
# GraphicUnitTest — AsyncSvgWidget integration (mock provider)
# ===========================================================================

@requires_graphics
class TestAsyncSvgWidgetIntegration(_SvgLoaderIsolation, GraphicUnitTest):
    '''Integration tests for AsyncSvgWidget using a mock SVG provider.'''

    def setUp(self):
        self._inject_mock_provider()
        super().setUp()

    def tearDown(self):
        self._restore_providers()
        super().tearDown()

    def test_load_from_bytes_reaches_ready_status(self):
        from kivy.uix.svg import AsyncSvgWidget
        w = AsyncSvgWidget(source=SIMPLE_SVG, size=(64, 64), size_hint=(None, None))
        self.render(w, framecount=1)
        self.assertEqual(w.status, 'ready')
        self.assertTrue(w.loaded)

    def test_error_status_on_missing_local_file(self):
        from kivy.uix.svg import AsyncSvgWidget
        errors = []
        w = AsyncSvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_error=lambda inst, msg: errors.append(msg))
        w.source = 'nonexistent_async_file.svg'
        # Error is set synchronously for local paths.
        self.assertEqual(w.status, 'error')
        self.assertTrue(errors)

    def test_stale_download_response_discarded(self):
        from kivy.uix.svg import AsyncSvgWidget
        w = AsyncSvgWidget(size=(64, 64), size_hint=(None, None))
        # Simulate: source was set to a URL, then changed before the response
        # arrived.  _pending_source reflects the new value.
        w._pending_source = SIMPLE_SVG

        class _FakeRequest:
            url = 'http://stale.example.com/old.svg'

        initial_status = w.status
        w._on_download_success(_FakeRequest(), b'<svg/>')
        # The stale response must be silently ignored.
        self.assertEqual(w.status, initial_status)

    def test_http_failure_sets_error_status(self):
        from kivy.uix.svg import AsyncSvgWidget
        errors = []
        w = AsyncSvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_error=lambda inst, msg: errors.append(msg))
        w._pending_source = 'http://example.com/icon.svg'

        class _FakeRequest:
            url = 'http://example.com/icon.svg'
            resp_status = 404

        w._on_download_failure(_FakeRequest(), None)
        self.assertEqual(w.status, 'error')
        self.assertTrue(errors)

    def test_network_error_sets_error_status(self):
        from kivy.uix.svg import AsyncSvgWidget
        errors = []
        w = AsyncSvgWidget(size=(64, 64), size_hint=(None, None))
        w.bind(on_error=lambda inst, msg: errors.append(msg))
        w._pending_source = 'http://example.com/icon.svg'

        class _FakeRequest:
            url = 'http://example.com/icon.svg'

        w._on_download_error(_FakeRequest(), ConnectionError('timeout'))
        self.assertEqual(w.status, 'error')
        self.assertTrue(errors)


if __name__ == '__main__':
    unittest.main()

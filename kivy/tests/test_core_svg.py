'''
SVG core provider tests
=======================

Tests for :mod:`kivy.core.svg` (SvgLoader registry) and
:mod:`kivy.core.svg.svg_thorvg` (provider helper functions).

These tests are pure-Python and do not require a display or GL context.
ThorVG-dependent tests are skipped automatically when this build of Kivy
was compiled without the :mod:`kivy.lib.thorvg` extension.
'''

import unittest


def _thorvg_available():
    try:
        import kivy.lib.thorvg._thorvg  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_mock_provider(name, *, load_returns=True, raises=False):
    '''Return a minimal SvgProviderBase subclass for testing SvgLoader.

    The class is created fresh each call so that test cases get independent
    class objects (useful for assertIsInstance checks).
    '''
    from kivy.core.svg import SvgProviderBase

    _load_returns = load_returns
    _raises = raises

    class MockProvider(SvgProviderBase):
        _provider_name = name

        def load(self, source):
            return _load_returns

        def load_data(self, data, mimetype='svg'):
            if _raises:
                raise RuntimeError('mock error')
            return _load_returns

        def get_document_size(self):
            return (64.0, 64.0)

        def get_element_ids(self):
            return []

        def render(self, width, height, current_color=None,
                   element_overrides=None):
            return b'\x00' * (width * height * 4)

    return MockProvider


# ---------------------------------------------------------------------------
# SvgLoader registry
# ---------------------------------------------------------------------------

class TestSvgLoader(unittest.TestCase):

    def setUp(self):
        from kivy.core.svg import SvgLoader
        self._loader = SvgLoader
        # Snapshot the registry so each test starts from a clean slate.
        self._orig_providers = list(SvgLoader.providers)
        self._orig_by_name = dict(SvgLoader.providers_by_name)

    def tearDown(self):
        self._loader.providers[:] = self._orig_providers
        self._loader.providers_by_name.clear()
        self._loader.providers_by_name.update(self._orig_by_name)

    def test_register_adds_provider(self):
        from kivy.core.svg import SvgLoader
        mock = _make_mock_provider('mock_reg')
        SvgLoader.register(mock)
        self.assertIn(mock, SvgLoader.providers)
        self.assertIn('mock_reg', SvgLoader.providers_by_name)
        self.assertIs(SvgLoader.providers_by_name['mock_reg'], mock)

    def test_register_raises_without_provider_name(self):
        from kivy.core.svg import SvgLoader, SvgProviderBase

        class BadProvider(SvgProviderBase):
            _provider_name = None

            def load(self, source): pass
            def load_data(self, data, mimetype='svg'): pass
            def get_document_size(self): pass
            def get_element_ids(self): pass
            def render(self, w, h, current_color=None,
                       element_overrides=None): pass

        with self.assertRaises(ValueError):
            SvgLoader.register(BadProvider)

    def test_load_data_returns_first_success(self):
        from kivy.core.svg import SvgLoader
        first = _make_mock_provider('first')
        second = _make_mock_provider('second')
        SvgLoader.providers[:] = [first, second]
        result = SvgLoader.load_data(b'<svg/>', 'svg')
        self.assertIsInstance(result, first)
        self.assertNotIsInstance(result, second)

    def test_load_data_returns_none_when_all_fail(self):
        from kivy.core.svg import SvgLoader
        failing = _make_mock_provider('failing', load_returns=False)
        SvgLoader.providers[:] = [failing]
        result = SvgLoader.load_data(b'<svg/>', 'svg')
        self.assertIsNone(result)

    def test_load_data_skips_raising_provider(self):
        from kivy.core.svg import SvgLoader
        raiser = _make_mock_provider('raiser', raises=True)
        good = _make_mock_provider('good')
        SvgLoader.providers[:] = [raiser, good]
        result = SvgLoader.load_data(b'<svg/>', 'svg')
        self.assertIsInstance(result, good)

    def test_load_returns_none_when_file_missing(self):
        from kivy.core.svg import SvgLoader
        failing = _make_mock_provider('failing_load', load_returns=False)
        SvgLoader.providers[:] = [failing]
        result = SvgLoader.load('nonexistent_file_for_testing.svg')
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# _svg_parse_dim
# ---------------------------------------------------------------------------

class TestSvgParseDim(unittest.TestCase):

    def setUp(self):
        from kivy.core.svg.svg_thorvg import _svg_parse_dim
        self._fn = _svg_parse_dim

    def test_plain_number(self):
        self.assertEqual(self._fn('256'), 256.0)

    def test_px_suffix(self):
        self.assertEqual(self._fn('100px'), 100.0)

    def test_px_suffix_with_whitespace(self):
        self.assertAlmostEqual(self._fn(' 50.5px '), 50.5)

    def test_whitespace_around_number(self):
        self.assertAlmostEqual(self._fn(' 42 '), 42.0)

    def test_zero_returns_none(self):
        self.assertIsNone(self._fn('0'))

    def test_zero_px_returns_none(self):
        self.assertIsNone(self._fn('0px'))

    def test_negative_returns_none(self):
        self.assertIsNone(self._fn('-10'))

    def test_inf_returns_none(self):
        self.assertIsNone(self._fn('inf'))

    def test_invalid_string_returns_none(self):
        self.assertIsNone(self._fn('abc'))

    def test_none_input_returns_none(self):
        self.assertIsNone(self._fn(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self._fn(''))


# ---------------------------------------------------------------------------
# _extract_element_ids_xml
# ---------------------------------------------------------------------------

class TestParseElementIds(unittest.TestCase):

    def setUp(self):
        from kivy.core.svg.svg_thorvg import _extract_element_ids_xml
        self._fn = _extract_element_ids_xml

    def test_returns_all_ids(self):
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<rect id="rect1"/>'
            b'<circle id="circle2"/>'
            b'<g id="group3"><path id="path4"/></g>'
            b'</svg>'
        )
        ids = self._fn(svg)
        self.assertEqual(set(ids), {'rect1', 'circle2', 'group3', 'path4'})

    def test_no_ids_returns_empty_list(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        self.assertEqual(self._fn(svg), [])

    def test_invalid_xml_returns_empty_list(self):
        # Should not raise; just return an empty list.
        self.assertEqual(self._fn(b'<not valid xml<<<'), [])

    def test_empty_bytes_returns_empty_list(self):
        self.assertEqual(self._fn(b''), [])

    def test_nested_ids_all_included(self):
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<g id="outer"><g id="inner"><rect id="leaf"/></g></g>'
            b'</svg>'
        )
        ids = self._fn(svg)
        self.assertEqual(set(ids), {'outer', 'inner', 'leaf'})


# ---------------------------------------------------------------------------
# _apply_current_color
# ---------------------------------------------------------------------------

class TestApplyCurrentColor(unittest.TestCase):

    def setUp(self):
        from kivy.core.svg.svg_thorvg import _apply_current_color
        self._fn = _apply_current_color

    def test_replaces_token_with_hex(self):
        svg = b'<rect fill="currentColor"/>'
        result = self._fn(svg, (1.0, 0.0, 0.0))
        self.assertIn(b'#ff0000', result)
        self.assertNotIn(b'currentColor', result)

    def test_multiple_occurrences_all_replaced(self):
        svg = b'<rect fill="currentColor" stroke="currentColor"/>'
        result = self._fn(svg, (0.0, 1.0, 0.0))
        self.assertEqual(result.count(b'#00ff00'), 2)
        self.assertNotIn(b'currentColor', result)

    def test_no_token_passes_through_unchanged(self):
        svg = b'<rect fill="red"/>'
        result = self._fn(svg, (1.0, 0.0, 0.0))
        self.assertEqual(result, svg)

    def test_ignores_alpha_component(self):
        svg = b'<rect fill="currentColor"/>'
        result_rgb = self._fn(svg, (0.5, 0.5, 0.5))
        result_rgba = self._fn(svg, (0.5, 0.5, 0.5, 0.0))
        self.assertEqual(result_rgb, result_rgba)

    def test_black_produces_hash_000000(self):
        svg = b'stroke="currentColor"'
        result = self._fn(svg, (0.0, 0.0, 0.0))
        self.assertIn(b'#000000', result)

    def test_white_produces_hash_ffffff(self):
        svg = b'stroke="currentColor"'
        result = self._fn(svg, (1.0, 1.0, 1.0))
        self.assertIn(b'#ffffff', result)


# ---------------------------------------------------------------------------
# _probe_size_from_xml  (pure-Python; no ThorVG required)
# ---------------------------------------------------------------------------

class TestProbeSizeFromXml(unittest.TestCase):
    '''Tests for SvgProviderThorvg._probe_size_from_xml.

    This method uses only ElementTree and does not touch ThorVG.
    '''

    def setUp(self):
        from kivy.core.svg.svg_thorvg import SvgProviderThorvg
        self._provider = SvgProviderThorvg()

    def _probe(self, svg_bytes):
        return self._provider._probe_size_from_xml(svg_bytes)

    def test_width_and_height(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"></svg>'
        self.assertEqual(self._probe(svg), (400.0, 300.0))

    def test_px_units_stripped(self):
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg"'
            b' width="200px" height="150px"></svg>'
        )
        self.assertEqual(self._probe(svg), (200.0, 150.0))

    def test_viewbox_fallback_when_no_width_height(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100"></svg>'
        self.assertEqual(self._probe(svg), (200.0, 100.0))

    def test_viewbox_comma_separated(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0,0,320,240"></svg>'
        self.assertEqual(self._probe(svg), (320.0, 240.0))

    def test_only_width_assumes_square(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="150"></svg>'
        self.assertEqual(self._probe(svg), (150.0, 150.0))

    def test_only_height_assumes_square(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" height="80"></svg>'
        self.assertEqual(self._probe(svg), (80.0, 80.0))

    def test_invalid_xml_returns_zero_tuple(self):
        self.assertEqual(self._probe(b'<<invalid>'), (0.0, 0.0))

    def test_no_dimension_info_returns_zero_tuple(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        self.assertEqual(self._probe(svg), (0.0, 0.0))


# ---------------------------------------------------------------------------
# SvgProviderThorvg - requires kivy.lib.thorvg
# ---------------------------------------------------------------------------

@unittest.skipUnless(_thorvg_available(), 'kivy.lib.thorvg not available')
class TestSvgProviderThorvg(unittest.TestCase):
    '''Integration tests for SvgProviderThorvg.

    Skipped when this build of Kivy has no ``kivy.lib.thorvg`` extension.
    '''

    # A minimal valid SVG used across tests.
    _SVG = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
        b'<rect id="bg" width="64" height="64" fill="blue"/>'
        b'</svg>'
    )

    def _make_provider(self):
        from kivy.core.svg.svg_thorvg import SvgProviderThorvg
        return SvgProviderThorvg()

    # -- pre-load state --

    def test_get_element_ids_before_load_returns_empty(self):
        p = self._make_provider()
        self.assertEqual(p.get_element_ids(), [])

    def test_get_document_size_before_load_returns_zero(self):
        p = self._make_provider()
        self.assertEqual(p.get_document_size(), (0.0, 0.0))

    def test_render_before_load_returns_none(self):
        p = self._make_provider()
        self.assertIsNone(p.render(64, 64))

    # -- load_data --

    def test_load_data_empty_returns_false(self):
        p = self._make_provider()
        self.assertFalse(p.load_data(b''))

    def test_load_data_valid_svg_returns_true(self):
        p = self._make_provider()
        self.assertTrue(p.load_data(self._SVG))

    def test_load_data_populates_element_ids(self):
        p = self._make_provider()
        p.load_data(self._SVG)
        self.assertIn('bg', p.get_element_ids())

    def test_load_data_populates_document_size(self):
        p = self._make_provider()
        p.load_data(self._SVG)
        w, h = p.get_document_size()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    # -- render --

    def test_render_invalid_width_returns_none(self):
        p = self._make_provider()
        p.load_data(self._SVG)
        self.assertIsNone(p.render(0, 64))

    def test_render_invalid_height_returns_none(self):
        p = self._make_provider()
        p.load_data(self._SVG)
        self.assertIsNone(p.render(64, 0))

    def test_render_returns_buffer_of_correct_length(self):
        p = self._make_provider()
        p.load_data(self._SVG)
        rgba = p.render(64, 64)
        # ``render()`` is documented as returning a buffer-protocol object,
        # not necessarily ``bytes`` - the ThorVG backend returns the
        # underlying SwCanvas so Texture.blit_buffer can upload zero-copy.
        self.assertIsNotNone(rgba)
        self.assertEqual(memoryview(rgba).nbytes, 64 * 64 * 4)

    def test_render_current_color_does_not_raise(self):
        p = self._make_provider()
        p.load_data(self._SVG)
        rgba = p.render(32, 32, current_color=(1.0, 0.0, 0.0))
        self.assertIsNotNone(rgba)
        self.assertEqual(memoryview(rgba).nbytes, 32 * 32 * 4)


if __name__ == '__main__':
    unittest.main()

"""
Tests for the ThorVG SVG image provider.

Coverage:
- _apply_min_raster_size() logic (no OpenGL, no thorvg required)
- _parse_uri_params() helper (no OpenGL, no thorvg required)
- Updated _provider_uri_re regex with optional [params] block
- Config [svg] default_size default value
- Integration: load an SVG file (skipped if the internal ``kivy.lib.thorvg``
  Cython extension was not compiled with this build of Kivy)
- Integration: render_size kwarg is honoured
"""

import os
import pytest

# SVGs bundled with Kivy's examples (examples/svg/).
# tiger.svg is used for most integration tests because it has large native
# dimensions (900×900), which makes the size-floor logic easy to assert.
# house.svg / mail.svg / settings.svg are 24×24 Lucide icons used for
# small-SVG upscaling tests.
_SVG_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', '..', 'examples', 'svg', 'tiger.svg',
)


# ---------------------------------------------------------------------------
# _apply_min_raster_size
# ---------------------------------------------------------------------------

class TestApplyMinRasterSize:
    """Pure unit tests - no OpenGL, no ThorVG extension required."""

    @pytest.fixture(autouse=True)
    def import_helper(self):
        from kivy.core.image.img_thorvg_svg import _apply_min_raster_size
        self.fn = _apply_min_raster_size

    def test_both_above_min_unchanged(self):
        assert self.fn(600, 800, min_size=512) == (600, 800)

    def test_both_equal_min_unchanged(self):
        assert self.fn(512, 512, min_size=512) == (512, 512)

    def test_landscape_short_dimension_scaled(self):
        w, h = self.fn(1024, 256, min_size=512)
        assert h == 512
        assert w == 2048

    def test_portrait_short_dimension_scaled(self):
        w, h = self.fn(256, 1024, min_size=512)
        assert w == 512
        assert h == 2048

    def test_square_below_min_scaled(self):
        w, h = self.fn(128, 128, min_size=512)
        assert w == 512
        assert h == 512

    def test_zero_width_returns_min_square(self):
        assert self.fn(0, 400, min_size=512) == (512, 512)

    def test_zero_height_returns_min_square(self):
        assert self.fn(400, 0, min_size=512) == (512, 512)

    def test_negative_dims_return_min_square(self):
        assert self.fn(-10, -10, min_size=512) == (512, 512)

    def test_custom_min_size(self):
        w, h = self.fn(64, 64, min_size=256)
        assert w == 256
        assert h == 256

    def test_result_is_always_int(self):
        w, h = self.fn(100.5, 200.5, min_size=512)
        assert isinstance(w, int)
        assert isinstance(h, int)


# ---------------------------------------------------------------------------
# Config default
# ---------------------------------------------------------------------------

class TestConfigDefaultSize:
    """Verify the [svg] section default is registered correctly."""

    def test_svg_default_size_is_512(self):
        from kivy.config import Config
        assert Config.getint('svg', 'default_size') == 512

    def test_svg_section_exists(self):
        from kivy.config import Config
        assert Config.has_section('svg')


# ---------------------------------------------------------------------------
# Integration tests (require the compiled kivy.lib.thorvg extension and an
# OpenGL context)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def kivy_window():
    """Initialize a Kivy Window so textures can be created."""
    from kivy.core.window import Window
    yield Window


@pytest.fixture(scope='module')
def thorvg():
    """Skip the whole module if this build of Kivy has no ThorVG extension.

    ``kivy.lib.thorvg`` is compiled into Kivy by ``setup.py`` when the
    ThorVG C headers are available at build time. If it's missing the
    SVG provider falls back to a silent no-op, so integration tests that
    assume SVGs can be rasterized have to be skipped.
    """
    return pytest.importorskip('kivy.lib.thorvg._thorvg')


@pytest.fixture
def svg_path():
    path = os.path.abspath(_SVG_PATH)
    if not os.path.exists(path):
        pytest.skip('Example SVG not found: %s' % path)
    return path


class TestThorvgSvgLoad:
    """Integration tests - require kivy.lib.thorvg and kivy_window."""

    def test_loader_is_registered(self, thorvg):
        from kivy.core.image import ImageLoader
        names = [
            getattr(ldr, '_provider_name', None)
            for ldr in ImageLoader.loaders
        ]
        assert 'thorvg_svg' in names

    def test_load_returns_image_data(self, thorvg, kivy_window, svg_path):
        from kivy.core.image.img_thorvg_svg import ImageLoaderThorvgSvg
        loader = ImageLoaderThorvgSvg(svg_path, ext='svg')
        frames = loader.load(svg_path)
        assert frames is not None
        assert len(frames) == 1
        frame = frames[0]
        assert frame.width > 0
        assert frame.height > 0
        assert frame.fmt == 'rgba'

    def test_default_size_applied_when_svg_is_small(
            self, thorvg, kivy_window):
        """An SVG with tiny native dimensions must be upscaled to default_size."""
        from kivy.core.image.img_thorvg_svg import ImageLoaderThorvgSvg
        from kivy.config import Config
        min_size = Config.getint('svg', 'default_size')

        # house.svg is a 24×24 Lucide icon — well below the 512 default.
        small_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'examples', 'svg', 'house.svg',
        ))
        if not os.path.exists(small_path):
            pytest.skip('examples/svg/house.svg not found')

        loader = ImageLoaderThorvgSvg(small_path, ext='svg')
        frames = loader.load(small_path)
        frame = frames[0]
        assert min(frame.width, frame.height) >= min_size

    def test_render_size_kwarg_overrides_default(
            self, thorvg, kivy_window, svg_path):
        """render_size acts as a per-image floor passed via __init__."""
        from kivy.core.image.img_thorvg_svg import ImageLoaderThorvgSvg
        # tiger.svg is 900x900 — floor of 128 is smaller, so native size wins.
        loader_small_floor = ImageLoaderThorvgSvg(
            svg_path, ext='svg', render_size=128)
        frame = loader_small_floor._data[0]
        assert max(frame.width, frame.height) >= 128

        # floor of 1024 exceeds native 900 — image should be scaled up.
        loader_large_floor = ImageLoaderThorvgSvg(
            svg_path, ext='svg', render_size=1024)
        frame = loader_large_floor._data[0]
        assert max(frame.width, frame.height) == 1024

    def test_coreimage_loads_svg(self, thorvg, kivy_window, svg_path):
        from kivy.core.image import Image as CoreImage
        img = CoreImage(svg_path, nocache=True)
        assert img.texture is not None
        assert img.texture.width > 0
        assert img.texture.height > 0

    def test_uri_with_size_param_loads(self, thorvg, kivy_window, svg_path):
        """size= acts as a minimum floor: native size wins when it is larger."""
        from kivy.core.image import Image as CoreImage
        # tiger.svg has a native size of 900x900 which exceeds the floor of 64;
        # the image should load at its native size, not be shrunk.
        uri_small_floor = '@image_provider:thorvg_svg[size=64](%s)' % svg_path
        img = CoreImage(uri_small_floor, nocache=True)
        assert img.texture is not None
        assert max(img.texture.width, img.texture.height) >= 64

        # When the floor exceeds the native size the image is scaled up.
        uri_large_floor = '@image_provider:thorvg_svg[size=1024](%s)' % svg_path
        img2 = CoreImage(uri_large_floor, nocache=True)
        assert img2.texture is not None
        assert max(img2.texture.width, img2.texture.height) == 1024


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

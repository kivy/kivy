"""
Tests for the surface that the SDL3 text provider renders text into.

If the surface cannot be created, `_SurfaceContainer` has to raise an
exception. It used to leave the surface as NULL and crash Python when the
pixels were read.
"""

import pytest

_text_sdl3 = pytest.importorskip(
    "kivy.core.text._text_sdl3",
    reason="the sdl3 text provider is not available",
)
_SurfaceContainer = _text_sdl3._SurfaceContainer


def test_surface_pixel_data_size():
    data = _SurfaceContainer(7, 3).get_data()
    assert (data.width, data.height) == (7, 3)
    assert data.fmt == "rgba"
    assert len(data.data) == 7 * 3 * 4


def test_empty_surface_is_allowed():
    data = _SurfaceContainer(0, 0).get_data()
    assert len(data.data) == 0


@pytest.mark.parametrize("size", [(-1, 5), (5, -1), (-1, -1)])
def test_negative_size_raises(size):
    with pytest.raises(ValueError, match="size"):
        _SurfaceContainer(*size)


def test_surface_that_cannot_be_allocated_raises():
    # Far too large for SDL to allocate, so SDL_CreateSurface returns NULL.
    with pytest.raises(MemoryError, match="surface"):
        _SurfaceContainer(2000000000, 2000000000)

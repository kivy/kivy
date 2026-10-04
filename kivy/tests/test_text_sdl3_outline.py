"""
Tests for text with an outline in the SDL3 text provider.

`font_blended=False` renders text with hard edges, without antialiasing.
That has to be true for the outline as well as for the text itself.
"""

import pytest

_text_sdl3 = pytest.importorskip(
    "kivy.core.text._text_sdl3",
    reason="the sdl3 text provider is not available",
)

OUTLINE_COLOR = (255, 0, 0)
TEXT_COLOR = (0, 255, 0)


def render(font_blended, outline_width):
    """Render a label and return the pixels as a list of (r, g, b, a)."""
    from kivy.core.text import LabelBase

    label_class = LabelBase.get_provider_class("sdl3")
    if label_class is None:
        pytest.skip("sdl3 text provider is not available")

    label = label_class(
        text="Hello",
        font_size=40,
        font_blended=font_blended,
        outline_width=outline_width,
        outline_color=(1, 0, 0, 1),
        color=(0, 1, 0, 1),
    )
    width, height = label.get_extents("Hello")
    surface = _text_sdl3._SurfaceContainer(
        width + 2 * outline_width, height + 2 * outline_width)
    surface.render(label, "Hello", 0, 0)
    data = surface.get_data().data
    return [tuple(data[i:i + 4]) for i in range(0, len(data), 4)]


def alpha_values(pixels):
    return {pixel[3] for pixel in pixels}


@pytest.mark.parametrize("outline_width", [0, 2])
def test_blended_text_is_antialiased(outline_width):
    assert not alpha_values(render(True, outline_width)) <= {0, 255}


@pytest.mark.parametrize("outline_width", [0, 2])
def test_not_blended_text_has_hard_edges(outline_width):
    assert alpha_values(render(False, outline_width)) <= {0, 255}


def test_not_blended_outline_keeps_outline_and_text_colors():
    opaque = {pixel[:3] for pixel in render(False, 2) if pixel[3] == 255}
    assert opaque == {OUTLINE_COLOR, TEXT_COLOR}


def test_blended_outline_keeps_outline_and_text_colors():
    opaque = {pixel[:3] for pixel in render(True, 2) if pixel[3] == 255}
    assert {OUTLINE_COLOR, TEXT_COLOR} <= opaque

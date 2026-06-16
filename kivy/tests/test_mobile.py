"""Tests for kivy.mobile and its platform dispatch.

These tests run on desktop (generic fallback) and verify the public API
contract without requiring an iOS or Android device.
"""

import pytest


class TestGenericFallback:
    """The generic (desktop) implementation must return safe defaults."""

    def test_get_dpi_returns_float(self):
        from kivy.mobile._platform.generic import get_dpi
        result = get_dpi()
        assert isinstance(result, float)
        assert result > 0

    def test_get_scale_returns_float(self):
        from kivy.mobile._platform.generic import get_scale
        result = get_scale()
        assert isinstance(result, float)
        assert result > 0

    def test_get_density_equals_scale(self):
        from kivy.mobile._platform.generic import get_density, get_scale
        assert get_density() == get_scale()

    def test_get_keyboard_height_is_zero(self):
        from kivy.mobile._platform.generic import get_keyboard_height
        assert get_keyboard_height() == 0.0

    def test_get_safe_area_keys(self):
        from kivy.mobile._platform.generic import get_safe_area
        sa = get_safe_area()
        assert set(sa.keys()) == {"top", "left", "bottom", "right"}
        for v in sa.values():
            assert isinstance(v, float)
            assert v == 0.0

    def test_subscribe_keyboard_height_is_noop(self):
        from kivy.mobile._platform.generic import subscribe_keyboard_height
        called = []
        subscribe_keyboard_height(lambda h: called.append(h))
        assert called == []

    def test_get_display_cutout_is_none(self):
        from kivy.mobile._platform.generic import get_display_cutout
        assert get_display_cutout() is None

    def test_get_system_bar_insets_is_none(self):
        from kivy.mobile._platform.generic import get_system_bar_insets
        assert get_system_bar_insets() is None


class TestPublicInterface:
    """kivy.mobile must export the full public API on all platforms."""

    _API = [
        "get_dpi",
        "get_scale",
        "get_density",
        "get_keyboard_height",
        "get_safe_area",
        "subscribe_keyboard_height",
        "get_display_cutout",
        "get_system_bar_insets",
    ]

    def test_all_symbols_importable(self):
        import kivy.mobile as m
        for name in self._API:
            assert hasattr(m, name), f"kivy.mobile missing: {name}"
            assert callable(getattr(m, name)), f"kivy.mobile.{name} not callable"

    def test_safe_area_shape(self):
        from kivy.mobile import get_safe_area
        sa = get_safe_area()
        assert isinstance(sa, dict)
        assert set(sa.keys()) == {"top", "left", "bottom", "right"}

    def test_keyboard_height_is_numeric(self):
        from kivy.mobile import get_keyboard_height
        h = get_keyboard_height()
        assert isinstance(h, (int, float))
        assert h >= 0

    def test_density_alias(self):
        from kivy.mobile import get_density, get_scale
        assert get_density() == get_scale()

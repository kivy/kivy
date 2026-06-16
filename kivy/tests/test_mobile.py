"""Tests for kivy.mobile and its platform implementations.

Since kivy.mobile raises ImportError on non-mobile platforms, these tests
load each _platform module directly by file path so the parent-package
ImportError guard does not interfere.
"""

import importlib.util
from pathlib import Path

import pytest

_PLATFORM_DIR = Path(__file__).parent.parent / "mobile" / "_platform"


def _load(name: str):
    """Load a kivy.mobile._platform module by filename, bypassing __init__."""
    path = _PLATFORM_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestIosPlatform:
    """Validate the iOS implementation module in isolation."""

    def test_all_functions_present(self):
        ios = _load("ios")
        for fn in (
            "get_dpi", "get_scale", "get_density",
            "get_keyboard_height", "get_safe_area",
            "subscribe_keyboard_height",
            "get_display_cutout", "get_system_bar_insets",
        ):
            assert hasattr(ios, fn), f"ios missing: {fn}"
            assert callable(getattr(ios, fn))

    def test_get_display_cutout_is_none(self):
        ios = _load("ios")
        assert ios.get_display_cutout() is None

    def test_get_system_bar_insets_is_none(self):
        ios = _load("ios")
        assert ios.get_system_bar_insets() is None


class TestAndroidPlatform:
    """Validate the Android placeholder module in isolation."""

    def test_all_functions_present(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            android = _load("android")
        for fn in (
            "get_dpi", "get_scale", "get_density",
            "get_keyboard_height", "get_safe_area",
            "subscribe_keyboard_height",
            "get_display_cutout", "get_system_bar_insets",
        ):
            assert hasattr(android, fn), f"android missing: {fn}"
            assert callable(getattr(android, fn))

    def test_placeholder_emits_warning(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _load("android")
        assert any(issubclass(x.category, UserWarning) for x in w)

    def test_placeholder_returns_safe_defaults(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            android = _load("android")
        assert android.get_dpi() == 96.0
        assert android.get_scale() == 1.0
        assert android.get_density() == 1.0
        assert android.get_keyboard_height() == 0.0
        sa = android.get_safe_area()
        assert set(sa.keys()) == {"top", "left", "bottom", "right"}
        assert all(v == 0.0 for v in sa.values())
        assert android.get_display_cutout() is None
        assert android.get_system_bar_insets() is None


class TestMobileImportError:
    """kivy.mobile must raise ImportError on non-mobile platforms."""

    def test_raises_on_desktop(self):
        import sys
        from kivy.utils import platform
        if platform in ('ios', 'android'):
            pytest.skip("running on mobile — ImportError not expected")
        sys.modules.pop("kivy.mobile", None)
        with pytest.raises(ImportError, match="mobile-only"):
            import kivy.mobile  # noqa: F401


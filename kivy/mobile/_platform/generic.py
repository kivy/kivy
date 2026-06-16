"""Desktop / unsupported-platform fallback for kivy.mobile.

Returns safe default values so app code that calls ``kivy.mobile`` APIs
works unchanged during desktop development and on any platform where a
real implementation is not yet available.

This module is imported automatically by ``kivy.mobile`` on all platforms
other than ``'ios'`` and ``'android'``.  Do not import it directly.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tier-1 API
# ---------------------------------------------------------------------------


def get_dpi() -> float:
    """Fallback DPI — asks the Window provider on desktop."""
    try:
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        return float(EventLoop.window.dpi)
    except Exception:
        return 96.0


def get_scale() -> float:
    """Fallback scale — derived from dpi/96 on desktop (matches legacy code)."""
    try:
        dpi = get_dpi()
        return dpi / 96.0
    except Exception:
        return 1.0


def get_density() -> float:
    """Alias for get_scale()."""
    return get_scale()


def get_keyboard_height() -> float:
    """Software keyboard height.  Always 0 on desktop."""
    return 0.0


def get_kheight() -> float:
    """Alias for get_keyboard_height()."""
    return 0.0


def get_safe_area() -> dict[str, float]:
    """Safe-area insets.  All zeros on desktop."""
    return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


def subscribe_keyboard_height(callback) -> None:
    """No-op on desktop; callback is accepted but never called."""
    pass


# ---------------------------------------------------------------------------
# Tier-2 API
# ---------------------------------------------------------------------------


def get_display_cutout():
    """Not applicable on desktop.  Always ``None``."""
    return None


def get_system_bar_insets():
    """Not applicable on desktop.  Always ``None``."""
    return None

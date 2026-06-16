"""Android placeholder for the kivy.mobile platform API.

.. warning:: **This module is a placeholder — it is not yet implemented.**

    A complete Android implementation requires the python-for-android (p4a)
    bootstrap to be refactored so that platform geometry (DPI, display
    density, keyboard height, safe-area / window insets) is exposed through
    a stable, Kivy-owned interface rather than through p4a's internal
    ``android`` and ``jnius`` modules.

    That refactor is tracked separately and must be approved by the p4a
    maintainers before this file can be filled in.

    Until then, all functions return the same safe defaults as the generic
    desktop fallback so that Android apps continue to run without crashing.

TODO (follow-up PR — depends on p4a bootstrap refactor):
    * get_dpi()              — read via jnius Hardware.getDPI() or AConfiguration NDK C API
    * get_scale()            — read via jnius Hardware.metrics.scaledDensity
    * get_keyboard_height()  — read via android.get_keyboard_height() (p4a module)
    * get_safe_area()        — read via WindowInsetsCompat system-gesture insets (API 29+)
    * get_display_cutout()   — read via DisplayCutout bounding rects (API 28+)
    * get_system_bar_insets() — read status-bar / nav-bar insets separately

This module is imported automatically by ``kivy.mobile`` when
``kivy.utils.platform == 'android'``.  Do not import it directly.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "kivy.mobile Android support is not yet implemented. "
    "All kivy.mobile calls will return safe fallback values. "
    "See kivy/mobile/_platform/android.py for details.",
    UserWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# Tier-1 API — safe fallbacks (mirrors generic.py until implemented)
# ---------------------------------------------------------------------------


def get_dpi() -> float:
    """Placeholder — returns 96.0 until Android support is implemented."""
    return 96.0


def get_scale() -> float:
    """Placeholder — returns 1.0 until Android support is implemented."""
    return 1.0


def get_density() -> float:
    """Alias for get_scale()."""
    return get_scale()


def get_keyboard_height() -> float:
    """Placeholder — returns 0.0 until Android support is implemented."""
    return 0.0


def get_safe_area() -> dict[str, float]:
    """Placeholder — returns all-zero insets until Android support is implemented."""
    return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


def subscribe_keyboard_height(callback) -> None:
    """Placeholder — no-op until Android support is implemented."""
    pass


# ---------------------------------------------------------------------------
# Tier-2 API — Android extras (not yet implemented)
# ---------------------------------------------------------------------------


def get_display_cutout():
    """Placeholder — returns None until Android support is implemented."""
    return None


def get_system_bar_insets():
    """Placeholder — returns None until Android support is implemented."""
    return None

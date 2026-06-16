"""Android placeholder for the kivy.mobile platform API.

.. warning:: **This module is a placeholder — it has not been tested on Android.**

    The implementations for ``get_dpi()``, ``get_scale()``, and
    ``get_keyboard_height()`` are straightforward — they use ``jnius``
    (a standalone Kivy-org package: https://github.com/kivy/pyjnius) and
    the ``android`` module provided by python-for-android, both of which
    are already present in every Kivy Android build.

    The placeholder exists because the implementation has not yet been
    tested on a real Android device.  Once validated locally or in CI,
    this file should be replaced with the working implementation.

TODO (follow-up PR — needs Android device or emulator to validate):
    * get_dpi()               — jnius: Hardware.getDPI()
    * get_scale()             — jnius: Hardware.metrics.scaledDensity
    * get_keyboard_height()   — android module: android.get_keyboard_height()
    * subscribe_keyboard_height() — drive from android keyboard events
    * get_safe_area()         — WindowInsetsCompat system-gesture insets (API 29+)
    * get_display_cutout()    — DisplayCutout bounding rects (API 28+)
    * get_system_bar_insets() — status-bar / nav-bar insets separated

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

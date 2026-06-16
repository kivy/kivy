"""Android implementation of the kivy.mobile platform API.

Provides the same interface as the iOS implementation; Android-specific
Tier-2 extras (display cutout, system bar insets) are also available.

Uses ``jnius`` to call Java/Android APIs via JNI.  ``jnius`` is always
present in a python-for-android build so there is no additional dependency.

This module is imported automatically by ``kivy.mobile`` when
``kivy.utils.platform == 'android'``.  Do not import it directly.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tier-1 API
# ---------------------------------------------------------------------------


def get_dpi() -> float:
    """Physical screen DPI via the Android Hardware jnius class."""
    try:
        import jnius
        Hardware = jnius.autoclass('org.renpy.android.Hardware')
        return float(Hardware.getDPI())
    except Exception:
        return 96.0


def get_scale() -> float:
    """Logical display density (scaledDensity) via the Android Hardware class."""
    try:
        import jnius
        Hardware = jnius.autoclass('org.renpy.android.Hardware')
        return float(Hardware.metrics.scaledDensity)
    except Exception:
        return 1.0


def get_density() -> float:
    """Alias for get_scale()."""
    return get_scale()


_kb_subscribers: list = []
_keyboard_height: float = 0.0


def get_keyboard_height() -> float:
    """Current software keyboard height in layout pixels (0 when hidden).

    Reads from the ``android`` platform module which is provided by the
    python-for-android bootstrap.
    """
    try:
        import android
        return float(android.get_keyboard_height())
    except Exception:
        return _keyboard_height


def subscribe_keyboard_height(callback) -> None:
    """Register *callback(height: float)* for keyboard height changes.

    .. note::
        On Android the callback is not yet driven by a native notification.
        Callers should poll ``get_keyboard_height()`` or bind to
        ``Window.keyboard_height`` which updates via Kivy's existing SDL3
        keyboard event path.
    """
    _kb_subscribers.append(callback)


def get_safe_area() -> dict[str, float]:
    """Safe-area insets in layout pixels.

    Returns ``{"top", "left", "bottom", "right"}``.

    On Android the safe area is approximated from the system-bar insets.
    A future iteration will read ``WindowInsetsCompat.getSystemGestureInsets``
    for a more precise value.
    """
    try:
        insets = get_system_bar_insets()
        if insets is None:
            return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}
        status = insets.get("status_bar", {})
        nav = insets.get("nav_bar", {})
        return {
            "top":    float(status.get("top", 0)),
            "left":   0.0,
            "bottom": float(nav.get("bottom", 0)),
            "right":  0.0,
        }
    except Exception:
        return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


# ---------------------------------------------------------------------------
# Tier-2 API — Android extras
# ---------------------------------------------------------------------------


def get_display_cutout():
    """Physical display-cutout bounding rects, or ``None`` if unavailable.

    Returns a list of ``{"left", "top", "right", "bottom"}`` dicts, one per
    physical cutout region.  Requires API 28+ and the
    ``android.display_cutout`` module from python-for-android.
    """
    try:
        from android import display_cutout  # type: ignore[import]
        return display_cutout.get_cutout_rects()
    except Exception:
        return None


def get_system_bar_insets():
    """Status-bar and navigation-bar insets separated, or ``None``.

    Returns::

        {
            "status_bar": {"top": float, "left": float, ...},
            "nav_bar":    {"top": float, "left": float, ...},
        }

    Requires the ``android.display_cutout`` module from python-for-android.
    """
    try:
        from android import display_cutout  # type: ignore[import]
        return display_cutout.get_system_bar_insets()
    except Exception:
        return None

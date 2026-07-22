"""kivy.mobile — platform-neutral bridge for mobile window/display geometry.

This module provides a stable, cross-platform API for runtime information that
Kivy's layout and metrics subsystems need on mobile platforms.  Internally it
dispatches to a platform-specific implementation in ``kivy.mobile._platform``.

.. note::
    ``kivy.mobile`` is a **mobile-only module**.  Importing it on desktop
    platforms (macOS, Windows, Linux) raises ``ImportError``.  Guard imports
    with ``if platform in {'ios', 'android'}:`` when writing code that also
    runs on desktop.

Public API — Tier 1 (always available on all platforms)
--------------------------------------------------------

.. code-block:: python

    from kivy.mobile import (
        get_dpi,
        get_scale,
        get_density,
        get_fontscale,
        get_keyboard_height,
        get_safe_area,
        subscribe_keyboard_height,
    )

``get_dpi()`` → float
    Physical screen DPI.

``get_scale()`` → float
    Display scale factor: UIKit *nativeScale* on iOS, ``DisplayMetrics.density``
    on Android.  This is the pure logical density; the user's font-scale
    preference is exposed separately as :attr:`kivy.metrics.Metrics.fontscale`.

``get_density()`` → float
    Alias for ``get_scale()``.

``get_fontscale()`` → float
    User font-scale preference feeding :attr:`kivy.metrics.Metrics.fontscale`.
    Android: ``Configuration.fontScale`` (typically 0.8-1.2).  iOS: always
    ``1.0`` (Dynamic Type has no single-scalar analogue).

``get_keyboard_height()`` → float
    Current software-keyboard height in layout points.  Returns 0 when hidden.
    (Android: requires API 30+; returns 0 below.)

``get_safe_area()`` → dict
    Safe-area insets in layout points (Android: requires API 30+; returns
    all-zero insets below)::

        {"top": float, "left": float, "bottom": float, "right": float}

    Covers the status bar / Dynamic Island (top), home-indicator (bottom),
    and notch / rounded-corner overhang (left / right in landscape).

``subscribe_keyboard_height(callback)``
    Register *callback(height: float)* to be called whenever the keyboard
    frame changes.  Called with 0.0 when the keyboard hides.

Public API — Tier 2 (Android platform extras)
---------------------------------------------

``get_display_cutout()`` → list[dict] | None
    Android physical display-cutout regions (requires API 28+; ``None`` below).
    Always ``None`` on iOS / desktop.

``get_system_bar_insets()`` → dict | None
    Android status-bar / navigation-bar insets separated (requires API 30+;
    ``None`` below).  Always ``None`` on iOS / desktop.

.. versionadded:: 3.0.0
"""

from __future__ import annotations

from kivy.utils import platform

if platform == 'ios':
    from kivy.mobile._platform.ios import (  # noqa: F401
        get_dpi,
        get_scale,
        get_density,
        get_fontscale,
        get_keyboard_height,
        get_safe_area,
        subscribe_keyboard_height,
        get_display_cutout,
        get_system_bar_insets,
    )
elif platform == 'android':
    from kivy.mobile._platform.android import (  # noqa: F401
        get_dpi,
        get_scale,
        get_density,
        get_fontscale,
        get_keyboard_height,
        get_safe_area,
        subscribe_keyboard_height,
        get_display_cutout,
        get_system_bar_insets,
    )
else:
    raise ImportError(
        f"kivy.mobile is a mobile-only module (platform={platform!r}). "
        "It is not available on desktop platforms. "
        "Guard your import with: if platform in {'ios', 'android'}: ..."
    )

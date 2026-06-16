"""kivy.mobile — platform-neutral bridge for mobile window/display geometry.

This module provides a stable, cross-platform API for runtime information that
Kivy's layout and metrics subsystems need on mobile platforms.  Internally it
dispatches to a platform-specific implementation in ``kivy.mobile._platform``.

Public API — Tier 1 (always available on all platforms)
--------------------------------------------------------

.. code-block:: python

    from kivy.mobile import (
        get_dpi,
        get_scale,
        get_density,
        get_keyboard_height,
        get_kheight,
        get_safe_area,
        subscribe_keyboard_height,
    )

``get_dpi()`` → float
    Physical screen DPI.

``get_scale()`` → float
    Display scale factor (UIKit *nativeScale* on iOS, *scaledDensity* on Android).

``get_density()`` → float
    Alias for ``get_scale()``.

``get_keyboard_height()`` → float
    Current software-keyboard height in layout points.  Returns 0 when hidden.

``get_kheight()`` → float
    Alias for ``get_keyboard_height()``.

``get_safe_area()`` → dict
    Safe-area insets in layout points::

        {"top": float, "left": float, "bottom": float, "right": float}

    Covers the status bar / Dynamic Island (top), home-indicator (bottom),
    and notch / rounded-corner overhang (left / right in landscape).

``subscribe_keyboard_height(callback)``
    Register *callback(height: float)* to be called whenever the keyboard
    frame changes.  Called with 0.0 when the keyboard hides.

Public API — Tier 2 (platform extras)
--------------------------------------

``get_display_cutout()`` → list[dict] | None
    Android physical display-cutout regions.  Always ``None`` on iOS / desktop.

``get_system_bar_insets()`` → dict | None
    Android status-bar / navigation-bar insets separated.  Always ``None`` on
    iOS / desktop.

.. versionadded:: 3.0.0
"""

from __future__ import annotations

from kivy.utils import platform

if platform == 'ios':
    from kivy.mobile._platform.ios import (  # noqa: F401
        get_dpi,
        get_scale,
        get_density,
        get_keyboard_height,
        get_kheight,
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
        get_keyboard_height,
        get_kheight,
        get_safe_area,
        subscribe_keyboard_height,
        get_display_cutout,
        get_system_bar_insets,
    )
else:
    from kivy.mobile._platform.generic import (  # noqa: F401
        get_dpi,
        get_scale,
        get_density,
        get_keyboard_height,
        get_kheight,
        get_safe_area,
        subscribe_keyboard_height,
        get_display_cutout,
        get_system_bar_insets,
    )

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

Public API — Tier 3 (Android bootstrap contract)
------------------------------------------------

Android-only, and unlike Tiers 1 it has no iOS counterpart: iOS has no
bootstrap in this sense.  See ``kivy.mobile._platform.android``
for the full contract.

Kivy holds no Android bootstrap class name.  Instead the bootstrap — whoever
*builds* the APK, be that python-for-android, kivyforge or a custom one — ships
a top-level ``_kivy_bootstrap`` module, which Kivy imports on first use:

``_kivy_bootstrap.get_activity()`` → Activity | None
    **Required.**  The current ``android.app.Activity``, or ``None`` where none
    exists (a background service).  Kivy calls it live on every access, so the
    bootstrap need do nothing when Android recreates the Activity.

``_kivy_bootstrap.get_context()`` → Context | None
    **Optional.**  For a context that never has an Activity.  When absent, the
    Application context is derived from the current Activity.

Applications read these through:

``get_activity()`` / ``get_app_context()``
    The current Activity / a usable Context.  Both raise
    ``ActivityProviderMissing`` when the bootstrap supplied no activity source,
    rather than silently returning defaults.

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
        # Tier 3 — bootstrap contract. Android-only by nature, so these are
        # deliberately absent from the iOS branch above.
        ActivityProviderMissing,
        get_activity,
        get_app_context,
    )
else:
    raise ImportError(
        f"kivy.mobile is a mobile-only module (platform={platform!r}). "
        "It is not available on desktop platforms. "
        "Guard your import with: if platform in {'ios', 'android'}: ..."
    )

"""Android implementation of the kivy.mobile platform API.

Reads runtime window/display geometry from the running Android activity using
``jnius`` (https://github.com/kivy/pyjnius) — a standalone Kivy-org package
present in every Kivy Android build.  No compiled extension and no
python-for-android module changes are required: every value is obtained by
reflection against ``PythonActivity.mActivity`` and the Android framework.

All lengths are returned in **pixels**, which is Kivy's layout coordinate
system on Android (``density`` is folded into :class:`kivy.metrics.Metrics`,
not into window coordinates).

Window-insets and display-cutout reads must run on the Android UI thread —
Kivy/SDL runs on a separate thread — so those calls are marshalled onto the UI
thread via ``Activity.runOnUiThread`` and block briefly for the result.
``DisplayMetrics`` is thread-safe to read directly.

Per-feature Android API requirements (method resolution happens at runtime via
reflection, so the build/compile API level is irrelevant — only the device's
runtime API matters):

* ``get_dpi`` / ``get_scale`` / ``get_density`` — all API levels
  (``DisplayMetrics``).
* ``get_display_cutout`` — API 28+ (Android 9); uses ``getDisplayCutout()`` and
  ``DisplayCutout.getBoundingRects()``.  Returns ``None`` below API 28.
* ``get_keyboard_height`` / ``get_safe_area`` / ``get_system_bar_insets`` —
  API 30+ (Android 11); use ``WindowInsets.getInsets(type)`` and the typed
  ``ime()`` / ``systemBars()`` / ``displayCutout()`` insets added in API 30.

On older devices the module still imports and the lower-API getters keep
working; the higher-API getters degrade to zeros/``None`` and emit a one-time
warning.  A clean API-30 baseline is intentional: legacy pre-30 inset APIs are
deprecated/heuristic, and Android 11+ covers the overwhelming majority of
active devices.

Android bootstrap contract
--------------------------
Everything else this backend touches is stock Android framework, but one symbol
must be supplied by the *Android bootstrap* (python-for-android today, and any
alternative such as a kivyforge bootstrap must provide an equivalent).  Keep
this in sync when adding bootstrap-coupled features:

* ``org.kivy.android.PythonActivity`` (class, see :data:`_ACTIVITY_CLASS`) with
  a static ``mActivity`` field holding the current ``android.app.Activity``.
  **Hard requirement** — the whole backend resolves geometry through it; if the
  bootstrap renames or omits it, the module degrades to safe defaults on import.

This module is imported automatically by ``kivy.mobile`` when
``kivy.utils.platform == 'android'``.  Do not import it directly.
"""

from __future__ import annotations

import threading

# The single bootstrap-provided activity class this backend depends on. Hoisted
# to a named constant so the one hard coupling to the Android bootstrap is an
# obvious, documented point rather than a bare string (see the module docstring,
# "Android bootstrap contract").
_ACTIVITY_CLASS = "org.kivy.android.PythonActivity"

try:
    from jnius import autoclass, PythonJavaClass, java_method

    PythonActivity = autoclass(_ACTIVITY_CLASS)
    DisplayMetrics = autoclass("android.util.DisplayMetrics")
    _Build_VERSION = autoclass("android.os.Build$VERSION")
except Exception:  # noqa: BLE001
    # ``jnius`` — and the Android framework classes it reflects — only exist in
    # an actual Android build.  Importing this module off-device must not hard
    # fail: Kivy's test-suite loads every ``kivy.mobile._platform`` backend
    # directly (bypassing the ``kivy.mobile`` desktop ImportError guard) to get
    # coverage, and pip-installing pyjnius alone would not help because
    # ``autoclass("org.kivy.android.PythonActivity")`` cannot resolve on a
    # desktop JVM.  Every getter below already falls back to a documented safe
    # default, so we degrade the whole module the same way when the runtime is
    # absent.
    autoclass = None
    PythonActivity = None
    DisplayMetrics = None
    _Build_VERSION = None

    def java_method(*_args, **_kwargs):
        def _decorator(func):
            return func

        return _decorator

    class PythonJavaClass:  # minimal stand-in so ``_Runnable`` can be defined
        pass

# ``WindowInsets.Type`` (and ``WindowInsets.getInsets(type)``) were added in API
# 30, so resolve the class lazily.  This keeps the module importable — and the
# lower-API reads (dpi/scale/density at any level, get_display_cutout at API
# 28+) working — on older devices, where only the typed-inset getters
# (keyboard height, safe area, system-bar insets) degrade to zeros/None.
_WindowInsetsType = None
_wit_resolved = False


def _window_insets_type():
    """Return ``android.view.WindowInsets$Type``, or ``None`` on API < 30.

    Emits a one-time warning the first time the class is found to be missing.
    """
    global _WindowInsetsType, _wit_resolved
    if not _wit_resolved:
        _wit_resolved = True
        try:
            _WindowInsetsType = autoclass("android.view.WindowInsets$Type")
        except Exception:  # noqa: BLE001 — class absent on API < 30
            from kivy.logger import Logger

            Logger.warning(
                "kivy.mobile: window-inset APIs require Android 11+ (API 30); "
                "keyboard height, safe area and system-bar insets will report "
                "zeros/None on this device (API %s)."
                % getattr(_Build_VERSION, "SDK_INT", "?")
            )
    return _WindowInsetsType


# Strong references to Runnables until the UI thread has executed them.
_runnable_refs: list = []


def _activity():
    return PythonActivity.mActivity


class _Runnable(PythonJavaClass):
    __javainterfaces__ = ["java/lang/Runnable"]
    __javacontext__ = "app"

    def __init__(self, func):
        super().__init__()
        self._func = func

    @java_method("()V")
    def run(self):
        self._func()


def _on_ui_thread(func, timeout: float = 2.0):
    """Run *func* on the Android UI thread and return its result (blocking)."""
    box: dict = {}
    done = threading.Event()

    def wrapper():
        try:
            box["value"] = func()
        except Exception as exc:  # noqa: BLE001
            box["error"] = exc
        finally:
            done.set()

    runnable = _Runnable(wrapper)
    _runnable_refs.append(runnable)
    try:
        _activity().runOnUiThread(runnable)
        if not done.wait(timeout=timeout):
            raise TimeoutError("kivy.mobile: UI-thread geometry read timed out")
        if "error" in box:
            raise box["error"]
        return box.get("value")
    finally:
        try:
            _runnable_refs.remove(runnable)
        except ValueError:
            pass


def _metrics():
    metrics = DisplayMetrics()
    _activity().getWindowManager().getDefaultDisplay().getMetrics(metrics)
    return metrics


def _root_insets():
    """WindowInsets for the decor view (call only on the UI thread)."""
    return _activity().getWindow().getDecorView().getRootWindowInsets()


# ---------------------------------------------------------------------------
# Tier-1 API
# ---------------------------------------------------------------------------


def get_dpi() -> float:
    """Physical screen DPI (Android ``densityDpi``; matches ``Metrics.dpi``)."""
    try:
        return float(_metrics().densityDpi)
    except Exception:
        return 96.0


def get_scale() -> float:
    """Display scale factor (Android ``DisplayMetrics.density``).

    This is the pure logical density (``densityDpi / 160``) that Kivy folds
    into :attr:`kivy.metrics.Metrics.density`.  It deliberately does **not**
    use ``scaledDensity`` (``density * fontScale``): the user's font-scale
    preference is exposed separately via :attr:`kivy.metrics.Metrics.fontscale`
    (read from ``Configuration.fontScale``), so using ``scaledDensity`` here
    would double-count it in ``dp``/layout sizing.
    """
    try:
        return float(_metrics().density)
    except Exception:
        return 1.0


def get_density() -> float:
    """Logical pixel density.  Alias for :func:`get_scale`."""
    return get_scale()


def get_fontscale() -> float:
    """User font-scale preference (Android ``Configuration.fontScale``).

    This is the accessibility text-size multiplier (typically 0.8-1.2) that
    Kivy applies to ``sp`` sizing through :attr:`kivy.metrics.Metrics.fontscale`.
    It is kept separate from :func:`get_scale` (which reports the pure logical
    density) so it is not double-counted in ``dp``/layout sizing.
    """
    try:
        config = _activity().getResources().getConfiguration()
        return float(config.fontScale)
    except Exception:
        return 1.0


def get_keyboard_height() -> float:
    """Current soft-keyboard (IME) height in pixels; 0 when hidden.

    Requires API 30+ (``WindowInsets.Type.ime()``); returns 0 below API 30.
    """

    def work():
        wit = _window_insets_type()
        insets = _root_insets()
        if wit is None or insets is None:
            return 0.0
        return float(insets.getInsets(wit.ime()).bottom)

    try:
        return _on_ui_thread(work)
    except Exception:
        return 0.0


def get_safe_area() -> dict[str, float]:
    """Safe-area insets in pixels (system bars unioned with the display cutout).

    Returns ``{"top", "left", "bottom", "right"}``.

    Requires API 30+ (typed ``WindowInsets`` insets); returns all-zero insets
    below API 30.
    """

    def work():
        wit = _window_insets_type()
        insets = _root_insets()
        if wit is None or insets is None:
            return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}
        bars = insets.getInsets(wit.systemBars())
        cut = insets.getInsets(wit.displayCutout())
        return {
            "top": float(max(bars.top, cut.top)),
            "left": float(max(bars.left, cut.left)),
            "bottom": float(max(bars.bottom, cut.bottom)),
            "right": float(max(bars.right, cut.right)),
        }

    try:
        return _on_ui_thread(work)
    except Exception:
        return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


# ---------------------------------------------------------------------------
# Keyboard-height subscription
#
# Driven by polling the IME inset from a Kivy Clock tick, scheduled lazily on
# the first subscription.  Subscribers are notified only when the height
# changes (including back to 0 on hide).
#
# The poll runs on the Kivy/SDL thread, so successive ticks never overlap
# (each read completes before the next tick), and each UI-thread hop normally
# returns in well under a millisecond.  Like the iOS notification observer, the
# subscription persists for the app's lifetime.
#
# Polling (rather than an event-driven Java listener) is a deliberate choice:
#   * python-for-android reached the same conclusion.  Its ``android`` module
#     once used a ``ViewTreeObserver.OnGlobalLayoutListener`` to cache the
#     height, but removed it (p4a commit f48feec4, "fix layout listener related
#     issues", #890) as "a processor intensive layout listener" that could
#     crash, switching to computing the height on demand.
#   * Evaluated on-device here (a ``View.OnApplyWindowInsetsListener`` proxy):
#     it yields values identical to the poll at comparable latency, fires only
#     at the animation's start/end (no per-frame smoothness — that needs a
#     separate ``WindowInsetsAnimation.Callback``), and adds a UI-thread
#     ``PythonJavaClass`` proxy whose only failure mode is severe (returning a
#     non-``WindowInsets`` value hard-crashes the UI thread inside
#     ``dispatchApplyWindowInsets``).
# A future enhancement could add a ``WindowInsetsAnimation.Callback`` if
# per-frame keyboard tracking is ever required, but the poll is simpler,
# testable off-device, and sufficient.
# ---------------------------------------------------------------------------

_kb_subscribers: list = []
_kb_last: float = 0.0
_kb_poll_scheduled: bool = False


def _poll_keyboard(_dt) -> None:
    global _kb_last
    height = get_keyboard_height()
    if height != _kb_last:
        _kb_last = height
        for cb in list(_kb_subscribers):
            # Isolate subscribers: one failing callback must not stop the
            # others or the poll loop, but log it so it is not lost silently.
            try:
                cb(height)
            except Exception:
                from kivy.logger import Logger

                Logger.exception(
                    "kivy.mobile: keyboard-height subscriber %r raised" % cb
                )


def subscribe_keyboard_height(callback) -> None:
    """Register *callback(height: float)* for keyboard-height changes.

    The callback runs on the Kivy main thread, so it is safe to update Kivy
    properties directly.  It is invoked with 0.0 when the keyboard hides.
    """
    global _kb_poll_scheduled
    if callback in _kb_subscribers:
        return
    _kb_subscribers.append(callback)
    if not _kb_poll_scheduled:
        from kivy.clock import Clock

        Clock.schedule_interval(_poll_keyboard, 1 / 10.0)
        _kb_poll_scheduled = True


# ---------------------------------------------------------------------------
# Tier-2 API — Android extras
# ---------------------------------------------------------------------------


def get_display_cutout():
    """Physical display-cutout regions, or ``None`` when the window has none.

    Returns a list of ``{"left", "top", "right", "bottom"}`` pixel rects (one
    per cutout).  Returns ``None`` when the current window does not overlap any
    cutout (e.g. when Android letterboxes the app away from it in landscape
    under the default cutout mode).

    Requires API 28+ (``getDisplayCutout()``); returns ``None`` below API 28.
    Unlike the safe-area/keyboard reads, this does not need the API-30 typed
    inset API.
    """

    def work():
        insets = _root_insets()
        if insets is None:
            return None
        cutout = insets.getDisplayCutout()
        if cutout is None:
            return None
        rects = cutout.getBoundingRects()
        out = []
        for i in range(rects.size()):
            r = rects.get(i)
            out.append(
                {
                    "left": int(r.left),
                    "top": int(r.top),
                    "right": int(r.right),
                    "bottom": int(r.bottom),
                }
            )
        return out or None

    try:
        return _on_ui_thread(work)
    except Exception:
        return None


def get_system_bar_insets():
    """Status-bar and navigation-bar insets separated, in pixels, or ``None``.

    Returns ``{"status_bar": {...}, "nav_bar": {...}}`` where each value is a
    ``{"left", "top", "right", "bottom"}`` dict.

    Requires API 30+ (typed ``statusBars()`` / ``navigationBars()`` insets);
    returns ``None`` below API 30, as pre-30 has no clean status-vs-nav split.
    """

    def work():
        wit = _window_insets_type()
        insets = _root_insets()
        if wit is None or insets is None:
            return None
        status = insets.getInsets(wit.statusBars())
        nav = insets.getInsets(wit.navigationBars())
        return {
            "status_bar": {
                "top": int(status.top),
                "left": int(status.left),
                "bottom": int(status.bottom),
                "right": int(status.right),
            },
            "nav_bar": {
                "top": int(nav.top),
                "left": int(nav.left),
                "bottom": int(nav.bottom),
                "right": int(nav.right),
            },
        }

    try:
        return _on_ui_thread(work)
    except Exception:
        return None

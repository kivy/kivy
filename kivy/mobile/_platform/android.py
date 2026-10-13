"""Android implementation of the kivy.mobile platform API.

Reads runtime window/display geometry from the running Android activity using
``jnius`` (https://github.com/kivy/pyjnius) — a standalone Kivy-org package
present in every Kivy Android build.  No compiled extension is required: every
value is obtained by reflection against the Android framework, starting from an
Activity the *bootstrap* supplies (see "Android bootstrap contract" below).
Kivy names no bootstrap class itself.

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
* ``move_task_to_back`` / ``finish_and_remove_task`` — all supported API levels
  (stock ``android.app.Activity`` methods).  ``remove_presplash`` needs no
  minimum API either, but is only as available as the bootstrap's own splash
  handling (see the bootstrap contract below).  These are app/task lifecycle
  actions rather than geometry reads; they are Android-only (no cross-platform
  analogue) so they are not surfaced through the neutral ``kivy.mobile`` API.

On older devices the module still imports and the lower-API getters keep
working; the higher-API getters degrade to zeros/``None`` and emit a one-time
warning.  A clean API-30 baseline is intentional: legacy pre-30 inset APIs are
deprecated/heuristic, and Android 11+ covers the overwhelming majority of
active devices.

Android bootstrap contract
--------------------------
Everything else this backend touches is stock Android framework, but the
Activity itself must come from the *Android bootstrap* — the component that
builds the APK and owns the Java activity class (python-for-android today, and
any alternative such as a kivyforge bootstrap).  Kivy defines the handshake and
holds no bootstrap class name; the bootstrap keeps that knowledge, which is
where it belongs, since it is the party that decides the class.  Keep this in
sync when adding bootstrap-coupled features:

* ``get_activity()`` on a top-level ``_kivy_bootstrap`` module (see
  :data:`_BOOTSTRAP_MODULE`), returning the current ``android.app.Activity``.
  **Hard requirement** — the whole backend resolves geometry through it.  This
  backend imports the module on first use; a build whose bootstrap ships no
  such module raises :class:`ActivityProviderMissing` rather than silently
  reporting default geometry.

  Kivy pulls rather than asking the bootstrap to register at startup, because
  registering would mean importing Kivy *before* the application runs, which
  fixes Kivy's ``KIVY_*`` environment and config before the app can set them.
  Pulling also means there is no ordering requirement to get wrong: the
  bootstrap only has to make the module importable.
* ``get_context()`` on the same module — **optional**, for a context that never
  has an Activity, such as a background service.  When absent,
  :func:`get_app_context` derives the Application context from the current
  Activity.
* ``remove_presplash()`` on the same module — **optional**, called once the
  first frame has been drawn so the bootstrap can dismiss its boot splash.
  Only Kivy knows when that moment is, which is why the call exists at all;
  *how* a splash is dismissed is the bootstrap's business and differs
  fundamentally between them (python-for-android removes a View it inserted;
  a bootstrap using the Android 12 system splash releases a keep-on-screen
  condition instead, which is not a method on the Activity).  A bootstrap with
  no splash to dismiss simply omits it and :func:`remove_presplash` does
  nothing.

Note that the Activity is *pulled* on every access, never cached: Android
recreates it on configuration changes and after process death, so a stored
instance both goes stale and pins a JNI reference to a dead Activity.  Because
nothing is registered or cached, this backend holds no mutable cross-thread
state beyond the one-time module import.

This module is imported automatically by ``kivy.mobile`` when
``kivy.utils.platform == 'android'``.  Do not import it directly.
"""

from __future__ import annotations

import threading
from importlib import import_module

# The module an Android bootstrap ships to satisfy Kivy's contract (see the
# module docstring, "Android bootstrap contract").  The name is Kivy-owned, so
# depending on it couples Kivy to no particular bootstrap; any bootstrap —
# python-for-android, kivyforge, or a custom one — may implement it.
_BOOTSTRAP_MODULE = "_kivy_bootstrap"

try:
    from jnius import autoclass, cast, PythonJavaClass, java_method

    DisplayMetrics = autoclass("android.util.DisplayMetrics")
    _Build_VERSION = autoclass("android.os.Build$VERSION")
except Exception:  # noqa: BLE001
    # ``jnius`` — and the Android framework classes it reflects — only exist in
    # an actual Android build.  Importing this module off-device must not hard
    # fail: Kivy's test-suite loads every ``kivy.mobile._platform`` backend
    # directly (bypassing the ``kivy.mobile`` desktop ImportError guard) to get
    # coverage.  Every geometry getter below falls back to a documented safe
    # default, so we degrade the whole module the same way when the runtime is
    # absent.
    autoclass = None
    cast = None
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


class ActivityProviderMissing(RuntimeError):
    """The Android bootstrap did not supply a way to reach the current Activity.

    Raised only when there *is* an Android runtime, so it always means a real
    build misconfiguration: the bootstrap that produced this APK does not
    satisfy Kivy's contract.  Deliberately not caught by the geometry getters,
    which would otherwise mask it as a plausible-looking default.
    """


class _AndroidRuntimeUnavailable(RuntimeError):
    """There is no Android runtime at all, so nothing can be resolved.

    Distinct from :class:`ActivityProviderMissing` because it is not an error
    to report to anyone: it is what happens when this backend is imported off
    device, which Kivy's own test-suite does deliberately.  The getters treat it
    like any other resolution failure and fall back to their documented
    defaults.
    """


_bootstrap = None
_bootstrap_resolved = False


def _bootstrap_module():
    """Import the bootstrap's contract module, once.

    Both outcomes are cached, including failure: a build whose bootstrap ships
    no such module must not pay for a failed import on every geometry read.

    Only ``ImportError`` is treated as "no bootstrap".  Anything else raised
    while importing is a fault in the bootstrap's own module and propagates, so
    it is not mistaken for an absent bootstrap.
    """
    global _bootstrap, _bootstrap_resolved
    if not _bootstrap_resolved:
        _bootstrap_resolved = True
        try:
            _bootstrap = import_module(_BOOTSTRAP_MODULE)
        except ImportError:
            _bootstrap = None
    return _bootstrap


def get_activity():
    """The current ``android.app.Activity``, pulled live from the bootstrap.

    Called afresh every time rather than cached: Android destroys and recreates
    the Activity on configuration changes (rotation, dark mode, locale,
    multi-window) and after process death, so a stored instance goes stale and
    holding one alive in a Python global pins a JNI reference to a dead
    Activity.  Pulling live self-heals for free.

    May legitimately return ``None`` where no Activity exists, such as in a
    background service.  Raises :class:`ActivityProviderMissing` when there is
    an Android runtime but the bootstrap supplied nothing — a build
    misconfiguration, so it is reported rather than papered over with a default.
    """
    module = _bootstrap_module()
    provider = getattr(module, "get_activity", None)
    if not callable(provider):
        if autoclass is None:
            raise _AndroidRuntimeUnavailable(
                "no Android runtime: jnius is unavailable, so there is no "
                "Activity to resolve"
            )
        raise ActivityProviderMissing(
            "No Android activity source available: this build's bootstrap "
            f"ships no {_BOOTSTRAP_MODULE!r} module exposing get_activity(). "
            "Kivy 3 requires the bootstrap to supply the current Activity. "
            "If you are using python-for-android, update it to a version that "
            "supports Kivy 3."
        )
    return provider()


def get_app_context():
    """A usable ``android.content.Context``, or ``None`` without an Activity.

    A bootstrap may optionally expose ``get_context()`` for contexts that never
    have an Activity — a background service, say.  Otherwise the Application
    context is derived from the current Activity, which is equivalent for
    everything Kivy uses a Context for.
    """
    provider = getattr(_bootstrap_module(), "get_context", None)
    if callable(provider):
        context = provider()
        if context is not None:
            return context
    activity = get_activity()
    return activity.getApplicationContext() if activity is not None else None


def _activity():
    return get_activity()


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


def run_on_ui_thread(func, *args, **kwargs):
    """Post *func* to the Android UI thread and return without waiting.

    The counterpart to :func:`_on_ui_thread`, which blocks for a result: use
    this where the caller only needs the call to land on the main thread, as
    Android requires for most framework calls.  Provided here so that callers
    elsewhere in Kivy need neither ``jnius`` boilerplate nor an Activity of
    their own — the Activity comes from the bootstrap contract above.
    """

    def wrapper():
        try:
            func(*args, **kwargs)
        finally:
            try:
                _runnable_refs.remove(runnable)
            except ValueError:
                pass

    runnable = _Runnable(wrapper)
    _runnable_refs.append(runnable)
    _activity().runOnUiThread(runnable)


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
    except ActivityProviderMissing:
        raise
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
    except ActivityProviderMissing:
        raise
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
    except ActivityProviderMissing:
        raise
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
    except ActivityProviderMissing:
        raise
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
    except ActivityProviderMissing:
        raise
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
    except ActivityProviderMissing:
        raise
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
    except ActivityProviderMissing:
        raise
    except Exception:
        return None


# ---------------------------------------------------------------------------
# App / task lifecycle
#
# Thin wrappers over stock ``android.app.Activity`` methods (plus the
# bootstrap-provided splash call), kept here so Kivy's cross-platform layers
# (App, Window, base) reach the Android bootstrap only through ``kivy.mobile``
# rather than importing the python-for-android ``android`` module directly.
# These are Android-only actions with no cross-platform analogue, so they live
# on this backend and are not exposed on the neutral ``kivy.mobile`` surface.
# Callers invoke them under a ``platform == 'android'`` guard.  They run on the
# calling (Kivy) thread, matching Kivy's long-standing behaviour for these
# calls.
# ---------------------------------------------------------------------------


def move_task_to_back() -> None:
    """Send the app's task to the background (Android "Home"-like behaviour).

    Wraps ``Activity.moveTaskToBack(true)``; used for the pause / back-gesture
    paths where the app should be backgrounded rather than destroyed.
    """
    _activity().moveTaskToBack(True)


def finish_and_remove_task() -> None:
    """Finish the app and remove it from the recents list.

    Wraps ``Activity.finishAndRemoveTask()``; used for the stop path so the
    Android task is torn down along with the Kivy app.
    """
    _activity().finishAndRemoveTask()


def remove_presplash() -> None:
    """Ask the bootstrap to dismiss its boot splash; a no-op if it has none.

    Kivy calls this once the first frame is drawn — the one thing about a boot
    splash that only Kivy knows.  The mechanism belongs to the bootstrap, so
    this delegates to an optional ``remove_presplash()`` on the contract module
    (see "Android bootstrap contract" above) rather than naming any bootstrap's
    method.

    Doing nothing is a correct outcome, not a swallowed error: a bootstrap may
    have no splash, or one the system dismisses by itself.  Bootstraps that do
    are expected to be idempotent — Kivy makes no promise about being called
    exactly once.
    """
    hook = getattr(_bootstrap_module(), "remove_presplash", None)
    if callable(hook):
        hook()


# ---------------------------------------------------------------------------
# App-private storage paths
#
# Android hands these out through the Context rather than as fixed paths, so
# they are resolved by reflection like everything else here.  Both are
# app-scoped, so the Application context and an Activity context give the same
# answer.  Unlike the geometry getters these have no safe default: a wrong path
# would silently write the user's data somewhere it will not be found again, so
# failures propagate.
# ---------------------------------------------------------------------------


def _context_path(getter: str):
    context = get_app_context()
    if context is None:
        return None
    return cast("java.io.File", getattr(context, getter)()).getAbsolutePath()


def get_files_dir():
    """Absolute path of the app's private files dir (``getFilesDir()``).

    ``None`` where there is no Context to ask.  Backs
    :attr:`kivy.app.App.user_data_dir` on Android.
    """
    return _context_path("getFilesDir")


def get_cache_dir():
    """Absolute path of the app's private cache dir (``getCacheDir()``).

    ``None`` where there is no Context to ask.  Backs
    :attr:`kivy.app.App.user_cache_dir` on Android.  Android may delete this
    directory's contents under storage pressure.
    """
    return _context_path("getCacheDir")

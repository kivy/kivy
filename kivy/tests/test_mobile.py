"""Tests for kivy.mobile and its platform implementations.

Since kivy.mobile raises ImportError on non-mobile platforms, these tests
load each _platform module directly by file path so the parent-package
ImportError guard does not interfere.
"""

import importlib.util
import sys
import types
from contextlib import contextmanager
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


# ---------------------------------------------------------------------------
# Fake jnius / Android runtime
#
# pyjnius is not installed off-device (and could not resolve the Android
# framework classes even if it were), so to exercise android.py's real
# reflection paths we install a fake ``jnius`` module in sys.modules that
# mimics just enough of the Android API surface the backend touches.
# ---------------------------------------------------------------------------


class _FakeInsets:
    def __init__(self, top=0, left=0, bottom=0, right=0):
        self.top, self.left, self.bottom, self.right = top, left, bottom, right


class _FakeRect:
    def __init__(self, left, top, right, bottom):
        self.left, self.top, self.right, self.bottom = left, top, right, bottom


class _FakeRectList:
    def __init__(self, rects):
        self._rects = rects

    def size(self):
        return len(self._rects)

    def get(self, i):
        return self._rects[i]


class _FakeCutout:
    def __init__(self, rects):
        self._rects = rects

    def getBoundingRects(self):
        return _FakeRectList(self._rects)


class _FakeWindowInsets:
    def __init__(self, mapping, cutout):
        self._mapping = mapping
        self._cutout = cutout

    def getInsets(self, key):
        return self._mapping[key]

    def getDisplayCutout(self):
        return self._cutout


class _FakeType:
    """Stand-in for ``android.view.WindowInsets$Type`` (static factory ints)."""

    @staticmethod
    def ime():
        return "ime"

    @staticmethod
    def systemBars():
        return "bars"

    @staticmethod
    def displayCutout():
        return "cut"

    @staticmethod
    def statusBars():
        return "status"

    @staticmethod
    def navigationBars():
        return "nav"


class _FakeDisplayMetrics:
    def __init__(self):
        self.densityDpi = 420
        # density is the pure logical scale (420/160); scaledDensity folds in
        # the user's font scale and must NOT be used for get_scale/get_density.
        self.density = 2.625
        self.scaledDensity = 3.0


class _FakeDisplay:
    def getMetrics(self, metrics):
        # Values are pre-populated on the _FakeDisplayMetrics instance.
        pass


class _FakeWindowManager:
    def getDefaultDisplay(self):
        return _FakeDisplay()


class _FakeDecorView:
    def __init__(self, insets):
        self._insets = insets

    def getRootWindowInsets(self):
        return self._insets


class _FakeWindow:
    def __init__(self, insets):
        self._insets = insets

    def getDecorView(self):
        return _FakeDecorView(self._insets)


class _FakeConfiguration:
    def __init__(self, font_scale=1.0):
        self.fontScale = font_scale


class _FakeResources:
    def __init__(self, font_scale=1.0):
        self._config = _FakeConfiguration(font_scale)

    def getConfiguration(self):
        return self._config


class _FakeActivity:
    def __init__(self, insets, font_scale=1.0):
        self._insets = insets
        self._resources = _FakeResources(font_scale)

    def runOnUiThread(self, runnable):
        # Run synchronously so the backend's UI-thread marshaling completes
        # in-process without a real looper.
        runnable.run()

    def getWindow(self):
        return _FakeWindow(self._insets)

    def getWindowManager(self):
        return _FakeWindowManager()

    def getResources(self):
        return self._resources


@contextmanager
def _fake_jnius(insets, sdk_int=33, missing=(), font_scale=1.0):
    """Install a fake ``jnius`` module and yield the freshly loaded backend.

    *missing* is a set of class names that ``autoclass`` should fail to
    resolve, used to simulate older API levels (e.g. no ``WindowInsets$Type``
    on API < 30).
    """

    class _FakePythonActivity:
        mActivity = _FakeActivity(insets, font_scale)

    class _FakeVersion:
        SDK_INT = sdk_int

    registry = {
        "org.kivy.android.PythonActivity": _FakePythonActivity,
        "android.util.DisplayMetrics": _FakeDisplayMetrics,
        "android.os.Build$VERSION": _FakeVersion,
        "android.view.WindowInsets$Type": _FakeType,
    }

    def _autoclass(name):
        if name in missing:
            raise Exception(f"class not found (simulated): {name}")
        return registry[name]

    def _java_method(*_a, **_k):
        def _deco(func):
            return func

        return _deco

    class _PythonJavaClass:
        pass

    module = types.ModuleType("jnius")
    module.autoclass = _autoclass
    module.java_method = _java_method
    module.PythonJavaClass = _PythonJavaClass

    saved = sys.modules.get("jnius")
    sys.modules["jnius"] = module
    try:
        yield _load("android")
    finally:
        if saved is None:
            sys.modules.pop("jnius", None)
        else:
            sys.modules["jnius"] = saved


@contextmanager
def _without_jnius():
    """Yield the backend loaded with ``jnius`` forced unavailable.

    Setting ``sys.modules['jnius'] = None`` makes ``import jnius`` raise
    ImportError regardless of whether pyjnius happens to be installed, so the
    off-device degradation path is exercised deterministically.
    """
    saved = sys.modules.get("jnius")
    sys.modules["jnius"] = None
    try:
        yield _load("android")
    finally:
        if saved is None:
            sys.modules.pop("jnius", None)
        else:
            sys.modules["jnius"] = saved


def _default_insets():
    cutout = _FakeCutout([_FakeRect(0, 0, 100, 120)])
    mapping = {
        "ime": _FakeInsets(bottom=800),
        "bars": _FakeInsets(top=100, bottom=150),
        "cut": _FakeInsets(top=120),
        "status": _FakeInsets(top=100),
        "nav": _FakeInsets(bottom=150),
    }
    return _FakeWindowInsets(mapping, cutout)


class TestIosPlatform:
    """Validate the iOS implementation module in isolation."""

    def test_all_functions_present(self):
        ios = _load("ios")
        for fn in (
            "get_dpi", "get_scale", "get_density", "get_fontscale",
            "get_keyboard_height", "get_safe_area",
            "subscribe_keyboard_height",
            "get_display_cutout", "get_system_bar_insets",
        ):
            assert hasattr(ios, fn), f"ios missing: {fn}"
            assert callable(getattr(ios, fn))

    def test_get_fontscale_is_one(self):
        # iOS Dynamic Type has no single-scalar analogue, so fontscale is 1.0.
        ios = _load("ios")
        assert ios.get_fontscale() == 1.0

    def test_get_display_cutout_is_none(self):
        ios = _load("ios")
        assert ios.get_display_cutout() is None

    def test_get_system_bar_insets_is_none(self):
        ios = _load("ios")
        assert ios.get_system_bar_insets() is None


class TestAndroidPlatform:
    """Validate the Android implementation module in isolation."""

    def test_all_functions_present(self):
        android = _load("android")
        for fn in (
            "get_dpi", "get_scale", "get_density", "get_fontscale",
            "get_keyboard_height", "get_safe_area",
            "subscribe_keyboard_height",
            "get_display_cutout", "get_system_bar_insets",
        ):
            assert hasattr(android, fn), f"android missing: {fn}"
            assert callable(getattr(android, fn))

    def test_imports_without_jnius(self):
        # jnius is absent off-device; the module must still import so the
        # test-suite can load it. ``autoclass`` degrades to None.
        with _without_jnius() as android:
            assert android.autoclass is None

    def test_degrades_without_android_runtime(self):
        # With no jnius/Android runtime every getter returns its documented
        # safe default rather than raising.
        with _without_jnius() as android:
            assert android.get_dpi() == 96.0
            assert android.get_scale() == 1.0
            assert android.get_density() == 1.0
            assert android.get_fontscale() == 1.0
            assert android.get_keyboard_height() == 0.0
            sa = android.get_safe_area()
            assert set(sa.keys()) == {"top", "left", "bottom", "right"}
            assert all(v == 0.0 for v in sa.values())
            assert android.get_display_cutout() is None
            assert android.get_system_bar_insets() is None

    def test_reads_metrics_via_reflection(self):
        with _fake_jnius(_default_insets()) as android:
            assert android.get_dpi() == 420.0
            # Must read DisplayMetrics.density (2.625), NOT scaledDensity (3.0),
            # so the user's font scale is not double-counted in dp/layout.
            assert android.get_scale() == 2.625
            assert android.get_density() == 2.625

    def test_fontscale_reads_configuration(self):
        # get_fontscale reflects Configuration.fontScale, kept separate from
        # get_scale so sp = density * fontscale without double-counting.
        with _fake_jnius(_default_insets(), font_scale=1.15) as android:
            assert android.get_fontscale() == 1.15
        # Defaults to 1.0 when the user has not changed the preference.
        with _fake_jnius(_default_insets()) as android:
            assert android.get_fontscale() == 1.0

    def test_keyboard_height_reads_ime_inset(self):
        with _fake_jnius(_default_insets()) as android:
            assert android.get_keyboard_height() == 800.0

    def test_safe_area_unions_system_bars_and_cutout(self):
        with _fake_jnius(_default_insets()) as android:
            # top = max(status/system-bar 100, cutout 120); bottom = 150.
            assert android.get_safe_area() == {
                "top": 120.0, "left": 0.0, "bottom": 150.0, "right": 0.0,
            }

    def test_system_bar_insets_separated(self):
        with _fake_jnius(_default_insets()) as android:
            insets = android.get_system_bar_insets()
            assert insets["status_bar"]["top"] == 100
            assert insets["nav_bar"]["bottom"] == 150

    def test_display_cutout_bounding_rects(self):
        with _fake_jnius(_default_insets()) as android:
            assert android.get_display_cutout() == [
                {"left": 0, "top": 0, "right": 100, "bottom": 120},
            ]

    def test_partial_degradation_on_api_29(self):
        # API 29: WindowInsets.Type is absent, so the typed-inset getters
        # degrade, but DisplayMetrics and display-cutout reads keep working.
        with _fake_jnius(
            _default_insets(),
            sdk_int=29,
            missing=("android.view.WindowInsets$Type",),
        ) as android:
            # Lower-API reads still work.
            assert android.get_dpi() == 420.0
            assert android.get_scale() == 2.625
            assert android.get_display_cutout() == [
                {"left": 0, "top": 0, "right": 100, "bottom": 120},
            ]
            # Typed-inset reads degrade to safe defaults.
            assert android.get_keyboard_height() == 0.0
            assert android.get_safe_area() == {
                "top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0,
            }
            assert android.get_system_bar_insets() is None

    def test_keyboard_subscription_notifies_on_change(self):
        insets = _default_insets()
        with _fake_jnius(insets) as android:
            # Avoid scheduling a real Clock interval; we drive _poll_keyboard
            # manually to test the change-detection logic.
            android._kb_poll_scheduled = True
            seen = []
            android.subscribe_keyboard_height(seen.append)

            # First poll: keyboard up at 800 -> notify.
            android._poll_keyboard(0)
            assert seen == [800.0]

            # No change -> no additional notification.
            android._poll_keyboard(0)
            assert seen == [800.0]

            # Keyboard hides -> notify with 0.
            insets._mapping["ime"] = _FakeInsets(bottom=0)
            android._poll_keyboard(0)
            assert seen == [800.0, 0.0]

    def test_subscribe_is_idempotent(self):
        with _fake_jnius(_default_insets()) as android:
            android._kb_poll_scheduled = True
            cb = lambda h: None  # noqa: E731
            android.subscribe_keyboard_height(cb)
            android.subscribe_keyboard_height(cb)
            assert android._kb_subscribers.count(cb) == 1

    def test_poll_isolates_raising_subscriber(self):
        # A subscriber raising must not stop later subscribers or the poll.
        with _fake_jnius(_default_insets()) as android:
            android._kb_poll_scheduled = True
            seen = []

            def boom(_h):
                raise RuntimeError("subscriber error")

            android.subscribe_keyboard_height(boom)
            android.subscribe_keyboard_height(seen.append)

            android._poll_keyboard(0)
            assert seen == [800.0]


class TestMobileImportError:
    """kivy.mobile must raise ImportError on non-mobile platforms."""

    def test_raises_on_desktop(self):
        import sys
        from kivy.utils import platform
        if platform in {'ios', 'android'}:
            pytest.skip("running on mobile — ImportError not expected")
        sys.modules.pop("kivy.mobile", None)
        with pytest.raises(ImportError, match="mobile-only"):
            import kivy.mobile  # noqa: F401


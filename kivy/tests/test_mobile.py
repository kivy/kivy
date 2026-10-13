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


class _FakeFile:
    def __init__(self, path):
        self._path = path

    def getAbsolutePath(self):
        return self._path


class _FakeContext:
    """Stands in for the process-stable Application ``Context``."""

    def getFilesDir(self):
        return _FakeFile("/data/user/0/org.test.app/files")

    def getCacheDir(self):
        return _FakeFile("/data/user/0/org.test.app/cache")


class _FakeActivity:
    def __init__(self, insets, font_scale=1.0):
        self._insets = insets
        self._resources = _FakeResources(font_scale)
        self._app_context = _FakeContext()
        self.moved_to_back = None
        self.finished = False
        self.presplash_removed = False

    def getApplicationContext(self):
        return self._app_context

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

    def moveTaskToBack(self, non_root):
        self.moved_to_back = non_root

    def finishAndRemoveTask(self):
        self.finished = True

    def removeLoadingScreen(self):
        self.presplash_removed = True


@contextmanager
def _fake_bootstrap(get_activity=None, get_context=None, remove_presplash=None):
    """Publish a fake ``_kivy_bootstrap`` module, as a real bootstrap would.

    Kivy resolves the Activity by importing this Kivy-named module from the
    bootstrap (see the backend's "Android bootstrap contract"), so faking the
    contract means publishing a module — there is nothing to register.  Passing
    neither function simulates a bootstrap that does not satisfy the contract.
    """
    module = types.ModuleType("_kivy_bootstrap")
    if get_activity is not None:
        module.get_activity = get_activity
    if get_context is not None:
        module.get_context = get_context
    if remove_presplash is not None:
        module.remove_presplash = remove_presplash

    saved = sys.modules.get("_kivy_bootstrap")
    sys.modules["_kivy_bootstrap"] = module
    try:
        yield module
    finally:
        if saved is None:
            sys.modules.pop("_kivy_bootstrap", None)
        else:
            sys.modules["_kivy_bootstrap"] = saved


@contextmanager
def _fake_jnius(insets, sdk_int=33, missing=(), font_scale=1.0, bootstrap=True):
    """Install fake ``jnius`` + bootstrap modules, yield the loaded backend.

    *missing* is a set of class names that ``autoclass`` should fail to
    resolve, used to simulate older API levels (e.g. no ``WindowInsets$Type``
    on API < 30).  Pass ``bootstrap=False`` to simulate an Android runtime whose
    bootstrap does not satisfy Kivy's contract; because discovery is lazy, a
    test may then supply its own via :func:`_fake_bootstrap`.

    Note there is no fake ``org.kivy.android.PythonActivity``: Kivy no longer
    knows any bootstrap class name, so the Activity arrives via the bootstrap
    module instead.  Tests reach it back through ``android.get_activity()``.
    """

    class _FakeVersion:
        SDK_INT = sdk_int

    registry = {
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
    # Real jnius re-types a Java object; the fakes are already Python objects,
    # so the signature is irrelevant here.
    module.cast = lambda _signature, obj: obj

    activity = _FakeActivity(insets, font_scale)

    saved = sys.modules.get("jnius")
    sys.modules["jnius"] = module
    try:
        if bootstrap:
            # Implements the splash hook the way python-for-android does, by
            # removing a view of its own; a bootstrap need not offer it at all.
            with _fake_bootstrap(
                get_activity=lambda: activity,
                remove_presplash=activity.removeLoadingScreen,
            ):
                yield _load("android")
        else:
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
            "move_task_to_back", "finish_and_remove_task", "remove_presplash",
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

    def test_move_task_to_back_calls_activity(self):
        # Backgrounds the task via Activity.moveTaskToBack(true).
        with _fake_jnius(_default_insets()) as android:
            android.move_task_to_back()
            assert android.get_activity().moved_to_back is True

    def test_finish_and_remove_task_calls_activity(self):
        # Tears the task down via Activity.finishAndRemoveTask().
        with _fake_jnius(_default_insets()) as android:
            android.finish_and_remove_task()
            assert android.get_activity().finished is True

    def test_remove_presplash_delegates_to_the_bootstrap(self):
        # Kivy supplies the timing (first frame drawn); the bootstrap supplies
        # the mechanism, here p4a-style view removal.
        with _fake_jnius(_default_insets()) as android:
            android.remove_presplash()
            assert android.get_activity().presplash_removed is True

    def test_storage_paths_come_from_the_context(self):
        # Backs App.user_data_dir / user_cache_dir, which used to reflect the
        # bootstrap's activity class directly from kivy/app.py.
        with _fake_jnius(_default_insets()) as android:
            assert android.get_files_dir() == "/data/user/0/org.test.app/files"
            assert android.get_cache_dir() == "/data/user/0/org.test.app/cache"

    def test_run_on_ui_thread_posts_to_activity(self):
        # Fire-and-forget marshaling, used by the clipboard provider.
        with _fake_jnius(_default_insets()) as android:
            seen = []
            android.run_on_ui_thread(seen.append, "posted")
            assert seen == ["posted"]
            # The Runnable must not be retained once it has run.
            assert android._runnable_refs == []

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


class TestAndroidBootstrapContract:
    """The handshake by which a bootstrap supplies the Activity.

    Kivy names no bootstrap class: it imports a Kivy-named ``_kivy_bootstrap``
    module and pulls from it, so python-for-android, kivyforge and custom
    bootstraps are all interchangeable here.
    """

    def test_kivy_holds_no_bootstrap_class_name(self):
        # A regression guard on the point of the whole contract: the backend
        # must not name any bootstrap's activity class.  Read the source rather
        # than importing it, for the same reason as the rest of this module.
        source = (_PLATFORM_DIR / "android.py").read_text(encoding="utf-8")
        assert "org.kivy.android" not in source
        # Nor any bootstrap-invented method name: removeLoadingScreen is
        # python-for-android's, and reaching for it here is what broke on
        # bootstraps that dismiss their splash some other way.
        assert "removeLoadingScreen" not in source

    def test_missing_bootstrap_raises(self):
        # A runtime is present but no bootstrap satisfies the contract: that is
        # a build misconfiguration, so it must be reported.
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with pytest.raises(android.ActivityProviderMissing,
                               match="_kivy_bootstrap"):
                android.get_activity()

    def test_bootstrap_without_get_activity_raises(self):
        # A module that exists but does not implement the contract is not
        # mistaken for a conforming one.
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with _fake_bootstrap():
                with pytest.raises(android.ActivityProviderMissing):
                    android.get_activity()

    def test_missing_bootstrap_is_not_masked_by_getter_defaults(self):
        # The geometry getters swallow reflection failures to return safe
        # defaults; that must not hide an unsatisfied contract, or the app runs
        # silently mis-scaled.
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with pytest.raises(android.ActivityProviderMissing):
                android.get_fontscale()

    def test_activity_is_pulled_live(self):
        # Android recreates the Activity on rotation and after process death,
        # so Kivy must re-ask every time rather than cache.
        current = {"activity": _FakeActivity(_default_insets())}
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with _fake_bootstrap(get_activity=lambda: current["activity"]):
                first = android.get_activity()
                current["activity"] = _FakeActivity(_default_insets())
                assert android.get_activity() is not first
                assert android.get_activity() is current["activity"]

    def test_service_may_have_no_activity(self):
        # A background service legitimately has no Activity; that is not an
        # error, and no Context can be derived from it.
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with _fake_bootstrap(get_activity=lambda: None):
                assert android.get_activity() is None
                assert android.get_app_context() is None

    def test_presplash_hook_is_optional(self):
        # A bootstrap whose splash the system dismisses by itself (or which has
        # none) implements nothing, and that must be silent rather than an
        # AttributeError one frame into the app.
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with _fake_bootstrap(get_activity=lambda: object()):
                android.remove_presplash()  # must not raise

    def test_presplash_hook_needs_no_activity(self):
        # The bootstrap owns the mechanism, so Kivy must not require an Activity
        # to exist just to ask: a system splash is not attached to one.
        called = []
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with _fake_bootstrap(get_activity=lambda: None,
                                 remove_presplash=lambda: called.append(True)):
                android.remove_presplash()
        assert called == [True]

    def test_optional_get_context_is_preferred(self):
        # Contexts with no Activity (a service) supply one directly.
        with _fake_jnius(_default_insets(), bootstrap=False) as android:
            with _fake_bootstrap(get_activity=lambda: None,
                                 get_context=lambda: "SERVICE_CONTEXT"):
                assert android.get_app_context() == "SERVICE_CONTEXT"

    def test_context_derived_from_activity_when_not_supplied(self):
        # The common case: a UI bootstrap implements only get_activity().
        with _fake_jnius(_default_insets()) as android:
            activity = android.get_activity()
            assert android.get_app_context() is activity.getApplicationContext()


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


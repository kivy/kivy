"""Tests for kivy.core.clipboard.clipboard_android.

``clipboard_android`` unconditionally does ``from jnius import autoclass`` and
``from kivy.mobile._platform.android import get_app_context,
run_on_ui_thread`` at module scope, so it cannot be imported off-device by
normal means: ``jnius`` is not installed, and importing ``kivy.mobile`` on a
non-mobile platform raises ``ImportError`` (see ``kivy/mobile/__init__.py``).

To exercise the module's own logic anyway, this installs fake ``jnius`` and
``kivy.mobile._platform.android`` modules in ``sys.modules`` and then loads
``clipboard_android.py`` directly by file path (the same technique used by
``kivy/tests/test_mobile.py`` for the platform backends).  The fakes here are
deliberately minimal: they only stand in for what ``_initialize_clipboard``
touches (``run_on_ui_thread`` and ``get_app_context``), not a full Android
runtime.
"""

import importlib.util
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).parent.parent / "core" / "clipboard" / "clipboard_android.py"
)


class _FakeVersion:
    SDK_INT = 33


class _FakeContext:
    CLIPBOARD_SERVICE = "clipboard"


def _autoclass(name):
    registry = {
        "java.lang.String": str,
        "android.content.Context": _FakeContext,
        "android.os.Build$VERSION": _FakeVersion,
    }
    return registry[name]


@contextmanager
def _fake_environment(run_on_ui_thread, get_app_context=None):
    """Install fake ``jnius``/backend modules, then load a fresh module.

    *run_on_ui_thread* controls whether/when the UI-thread callback actually
    runs, which is exactly what each test below needs to vary. *get_app_context*
    defaults to a stand-in that is never expected to be called (the timeout
    case never reaches it).
    """
    jnius_module = types.ModuleType("jnius")
    jnius_module.autoclass = _autoclass

    android_module = types.ModuleType("kivy.mobile._platform.android")
    android_module.run_on_ui_thread = run_on_ui_thread
    android_module.get_app_context = get_app_context or (
        lambda: pytest.fail("get_app_context() should not have been called")
    )

    affected = (
        "jnius",
        "kivy.mobile",
        "kivy.mobile._platform",
        "kivy.mobile._platform.android",
    )
    saved = {name: sys.modules.get(name) for name in affected}

    sys.modules["jnius"] = jnius_module
    sys.modules["kivy.mobile"] = types.ModuleType("kivy.mobile")
    sys.modules["kivy.mobile._platform"] = types.ModuleType("kivy.mobile._platform")
    sys.modules["kivy.mobile._platform.android"] = android_module

    try:
        spec = importlib.util.spec_from_file_location(
            "clipboard_android", _MODULE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        for name, mod in saved.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod


class _FakeClipboardManager:
    """Stands in for whatever ``getSystemService(CLIPBOARD_SERVICE)`` returns."""


class _FakeAppContext:
    def getSystemService(self, service):
        assert service == _FakeContext.CLIPBOARD_SERVICE
        return _FakeClipboardManager()


def _run_immediately(func, *args, **kwargs):
    """Fake ``run_on_ui_thread`` that runs *func* synchronously in-thread.

    Adequate for the success/failure cases: ``_initialize_clipboard`` only
    needs the callback to have run (and signalled ``done``) by the time it
    calls ``done.wait()``, which is just as true whether that happens on this
    thread or another.
    """
    func(*args, **kwargs)


def _never_run(func, *args, **kwargs):
    """Fake ``run_on_ui_thread`` that simulates a UI thread that never responds."""


class TestClipboardAndroidInitialize:
    def test_success_sets_clipboard_and_returns(self):
        with _fake_environment(
            run_on_ui_thread=_run_immediately,
            get_app_context=lambda: _FakeAppContext(),
        ) as module:
            clippy = module.ClipboardAndroid()
            clippy._initialize_clipboard()
            assert isinstance(module._clipboard, _FakeClipboardManager)

    def test_ui_thread_exception_is_reraised_on_the_caller(self):
        class Boom(Exception):
            pass

        def failing_get_app_context():
            raise Boom("no context available")

        with _fake_environment(
            run_on_ui_thread=_run_immediately,
            get_app_context=failing_get_app_context,
        ) as module:
            clippy = module.ClipboardAndroid()
            with pytest.raises(Boom, match="no context available"):
                clippy._initialize_clipboard()
            # The failed lookup must not leave a truthy-but-wrong clipboard.
            assert module._clipboard is None

    def test_times_out_when_ui_thread_never_responds(self):
        with _fake_environment(run_on_ui_thread=_never_run) as module:
            # Real UI-thread turnaround is milliseconds; shrink the timeout so
            # this test doesn't have to sleep for the production value.
            module._INIT_TIMEOUT = 0.05
            clippy = module.ClipboardAndroid()
            with pytest.raises(TimeoutError, match="timed out"):
                clippy._initialize_clipboard()
            assert module._clipboard is None

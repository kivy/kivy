import pytest
import os
import sys
# Choose async fixture decorator based on KIVY_EVENTLOOP and available plugins
_env_eventloop = os.environ.get('KIVY_EVENTLOOP', 'asyncio')
if _env_eventloop == 'asyncio':
    try:
        import pytest_asyncio
        _ASYNC_FIXTURE_DECORATOR = pytest_asyncio.fixture
    except ImportError:  # fallback if pytest-asyncio is missing
        _ASYNC_FIXTURE_DECORATOR = pytest.fixture
else:
    # For trio/other event loops, let the active plugin handle async functions
    _ASYNC_FIXTURE_DECORATOR = pytest.fixture
import gc
import weakref
import time
import os.path

__all__ = ('kivy_clock', 'kivy_metrics', 'kivy_exception_manager', 'kivy_app',
           'kivy_init')

@pytest.fixture()
def kivy_init():
    """A fixture to make sure that Kivy has all the global state it needs for testing

    Ensures that tests using this fixture will not receive real mouse, keyboard, or
    touchpad input. To mimic input, use :class:`kivy.tests.UnitTestTouch`.

    Suitable only for tests that use Kivy's internal event loop. `asyncio` and
    `trio` based apps need the `kivy_app` fixture.

    """
    from kivy.core.window import EventLoop, Window, stopTouchApp

    def clear_window_and_event_loop():
        for child in Window.children[:]:
            Window.remove_widget(child)
        Window.canvas.before.clear()
        Window.canvas.clear()
        Window.canvas.after.clear()
        EventLoop.touches.clear()
        for post_proc in EventLoop.postproc_modules:
            if hasattr(post_proc, "touches"):
                post_proc.touches.clear()
            elif hasattr(post_proc, "last_touches"):
                post_proc.last_touches.clear()

    from os import environ

    environ["KIVY_USE_DEFAULTCONFIG"] = "1"

    # force window size + remove all inputs
    from kivy.config import Config

    Config.set("graphics", "width", "320")
    Config.set("graphics", "height", "240")
    for items in Config.items("input"):
        Config.remove_option("input", items[0])

    # ensure our window is correctly created
    Window.create_window()
    Window.register()
    Window.initialized = True
    Window.close = lambda *s: None
    clear_window_and_event_loop()

    yield
    if EventLoop.status == "started":
        clear_window_and_event_loop()
        stopTouchApp()


@pytest.fixture()
def kivy_clock():
    from kivy.context import Context
    from kivy.clock import ClockBase

    context = Context(init=False)
    context['Clock'] = ClockBase()
    context.push()

    from kivy.clock import Clock
    Clock._max_fps = 0

    try:
        Clock.start_clock()
        yield Clock
        Clock.stop_clock()
    finally:
        context.pop()


@pytest.fixture()
def kivy_metrics():
    from kivy.context import Context
    from kivy.metrics import MetricsBase, Metrics
    from kivy._metrics import dispatch_pixel_scale

    context = Context(init=False)
    context['Metrics'] = MetricsBase()
    context.push()
    # need to do it to reset the global value
    dispatch_pixel_scale()

    try:
        yield Metrics
    finally:
        context.pop()
        Metrics._set_cached_scaling()


@pytest.fixture()
def kivy_exception_manager():
    from kivy.context import Context
    from kivy.base import ExceptionManagerBase, ExceptionManager

    context = Context(init=False)
    context['ExceptionManager'] = ExceptionManagerBase()
    context.push()

    try:
        yield ExceptionManager
    finally:
        context.pop()


# keep track of all the kivy app fixtures so that we can check that it
# properly dies
apps = []


# Async fixture, decorator chosen based on available plugin
@_ASYNC_FIXTURE_DECORATOR()
async def kivy_app(request, nursery):
    from kivy.base import stopTouchApp
    from kivy.app import App

    gc.collect()
    # Clean up any previous app that might still be hanging around
    if apps:
        last_app, last_request = apps.pop()
        leaked = last_app()
        if leaked is not None:
            # Log warning but don't fail - pytest 9 async fixtures may not
            # guarantee teardown completion before next test setup
            print(
                f"\nWarning: Previous app not released: {last_request}",
                file=sys.stderr,
            )
            stopTouchApp()
            App._running_app = None
            gc.collect()
            del leaked

    from os import environ
    environ['KIVY_USE_DEFAULTCONFIG'] = '1'

    # force window size + remove all inputs
    from kivy.config import Config
    Config.set('graphics', 'width', '320')
    Config.set('graphics', 'height', '240')
    for items in Config.items('input'):
        Config.remove_option('input', items[0])

    from kivy.core.window import Window
    from kivy.context import Context
    from kivy.clock import ClockBase
    from kivy.factory import FactoryBase, Factory
    from kivy.app import App
    from kivy.lang.builder import BuilderBase, Builder
    from kivy.base import stopTouchApp
    from kivy import kivy_data_dir
    from kivy.logger import LoggerHistory

    kivy_eventloop = environ.get('KIVY_EVENTLOOP', 'asyncio')
    if kivy_eventloop == 'asyncio':
        async_lib = 'asyncio'
    elif kivy_eventloop == 'trio':
        pytest.importorskip(
            'pytest_trio',
            reason='KIVY_EVENTLOOP == "trio" but '
                   '"pytest_trio" is not installed')
        async_lib = 'trio'
    else:
        pytest.skip(
            'KIVY_EVENTLOOP must be set to either of "asyncio" or '
            '"trio" to run async tests')

    context = Context(init=False)
    context['Clock'] = ClockBase(async_lib=async_lib)

    # have to make sure all global kv files are loaded before this because
    # globally read kv files (e.g. on module import) will not be loaded again
    # in the new builder, except if manually loaded, which we don't do
    context['Factory'] = FactoryBase.create_from(Factory)
    context['Builder'] = BuilderBase.create_from(Builder)
    context.push()

    Window.create_window()
    Window.register()
    Window.initialized = True
    Window.canvas.clear()

    app = request.param[0]()
    app.set_async_lib(async_lib)

    if async_lib == 'asyncio':
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(app.async_run())
    else:
        nursery.start_soon(app.async_run)
    from kivy.clock import Clock
    Clock._max_fps = 0

    ts = time.perf_counter()
    while not app.app_has_started:
        await app.async_sleep(.1)
        if time.perf_counter() - ts >= 10:
            raise TimeoutError()

    await app.wait_clock_frames(5)

    yield app

    # Comprehensive cleanup for pytest 9 async fixture compatibility
    from kivy.app import App
    stopTouchApp()
    App._running_app = None

    ts = time.perf_counter()
    while not app.app_has_stopped:
        await app.async_sleep(.1)
        if time.perf_counter() - ts >= 10:
            raise TimeoutError()

    for child in Window.children[:]:
        Window.remove_widget(child)
    context.pop()

    # Aggressively release all resources
    del context
    LoggerHistory.clear_history()

    # Store weakref for next test to check cleanup
    apps.append((weakref.ref(app), request))
    del app

    # Force garbage collection multiple times to ensure cleanup
    for _ in range(3):
        gc.collect()

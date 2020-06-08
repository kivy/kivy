import pytest
import gc
import weakref
import time
import os.path

__all__ = ('kivy_clock', 'kivy_exception_manager', 'kivy_app', )


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


@pytest.fixture()
async def kivy_app(request, nursery):
    gc.collect()
    if apps:
        last_app, last_request = apps.pop()
        assert last_app() is None, \
            'Memory leak: failed to release app for test ' + repr(last_request)

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
        pytest.importorskip(
            'pytest_asyncio',
            reason='KIVY_EVENTLOOP == "asyncio" but '
                   '"pytest_asyncio" is not installed')
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

    stopTouchApp()

    ts = time.perf_counter()
    while not app.app_has_stopped:
        await app.async_sleep(.1)
        if time.perf_counter() - ts >= 10:
            raise TimeoutError()

    for child in Window.children[:]:
        Window.remove_widget(child)
    context.pop()

    # release all the resources
    del context
    LoggerHistory.clear_history()
    apps.append((weakref.ref(app), request))
    del app
    gc.collect()

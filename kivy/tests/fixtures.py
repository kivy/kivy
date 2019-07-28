import pytest
import gc
import weakref
import time
import os.path
from kivy.tests import async_sleep

__all__ = ('kivy_app', )

# keep track of all the kivy app fixtures so that we can check that it
# properly dies
apps = []


@pytest.fixture()
async def kivy_app(request, nursery):
    gc.collect()
    if apps:
        last_app = apps.pop()
        assert last_app() is None

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
    from kivy.lang.builder import BuilderBase, Builder
    from kivy.base import stopTouchApp
    from kivy import kivy_data_dir

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
            reason='KIVY_EVENTLOOP must be set to either of "asyncio" or '
                   '"trio" to run async tests')

    context = Context(init=False)
    context['Clock'] = ClockBase(async_lib=async_lib)
    # context['Builder'] = BuilderBase()
    context.push()
    # Builder.load_file(
    #     os.path.join(kivy_data_dir, 'style.kv'), rulesonly=True)

    Window.create_window()
    Window.register()
    Window.initialized = True
    Window.canvas.clear()

    app = request.param[0]()

    if async_lib == 'asyncio':
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(app.async_run())
    else:
        nursery.start_soon(app.async_run)

    ts = time.perf_counter()
    while not app.app_has_started:
        await async_sleep(.1)
        if time.perf_counter() - ts >= 10:
            raise TimeoutError()

    await app.wait_clock_frames(5)

    yield app

    stopTouchApp()

    ts = time.perf_counter()
    while not app.app_has_stopped:
        await async_sleep(.1)
        if time.perf_counter() - ts >= 10:
            raise TimeoutError()

    for child in Window.children[:]:
        Window.remove_widget(child)
    context.pop()

    # release all the resources
    del context
    apps.append(weakref.ref(app))
    del app
    gc.collect()
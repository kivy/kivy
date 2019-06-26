import pytest
from functools import wraps
import gc
import asyncio
import time
import os.path
from kivy.graphics.cgl import cgl_get_backend_name

try:
    import pytest_asyncio
    async_sleep = asyncio.sleep
except ImportError:
    try:
        from pytest_trio import trio_fixture
        import trio
        async_sleep = trio.sleep
    except ImportError:
        pass
else:
    @pytest.fixture()
    def nursery():
        pass


def pytest_runtest_makereport(item, call):
    # from https://docs.pytest.org/en/latest/example/simple.html
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    # from https://docs.pytest.org/en/latest/example/simple.html
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


def async_run(func=None, app_cls_func=None):
    def inner_func(func):
        if 'mock' == cgl_get_backend_name():
            return pytest.mark.skip(
                reason='Skipping because gl backend is set to mock')(func)

        try:
            import kivy.tests.async_common
        except SyntaxError:
            return pytest.mark.skip(
                reason='Skipping because graphics tests are not supported on '
                       'py3.5, only on py3.6+')(func)

        if app_cls_func is not None:
            func = pytest.mark.parametrize(
                "kivy_app", [[app_cls_func], ], indirect=True)(func)

        try:
            import pytest_asyncio
            return pytest.mark.asyncio(func)
        except ImportError:
            try:
                import trio
                from pytest_trio import trio_fixture
                func._force_trio_fixture = True
                return func
            except ImportError:
                return pytest.mark.skip(
                    reason='Either pytest_asyncio or pytest_trio must be '
                    'installed to run asyncio tests')(func)

    if func is None:
        return inner_func

    return inner_func(func)


@pytest.fixture()
async def kivy_app(request, nursery):
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

    try:
        import pytest_asyncio
        async_lib = 'async'
    except ImportError:
        try:
            import trio
            from pytest_trio import trio_fixture
            async_lib = 'trio'
        except ImportError:
            pytest.skip(
                'Either pytest_asyncio or pytest_trio must be installed to '
                'run asyncio tests')
            return

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

    if async_lib == 'async':
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
    gc.collect()

import pytest
from string import ascii_letters
from random import randint
import gc

import sys


@pytest.fixture
def kivy_benchmark(benchmark, kivy_clock):
    from kivy.core.window import Window
    from kivy.cache import Cache
    from kivy.utils import platform
    import kivy
    from kivy.core.gl import glGetString, GL_VENDOR, GL_RENDERER, GL_VERSION

    for category in list(Cache._objects.keys()):
        if category not in Cache._categories:
            continue

        for key in list(Cache._objects[category].keys()):
            Cache.remove(category, key)

    gc.collect()

    benchmark.extra_info['platform'] = str(sys.platform)
    benchmark.extra_info['python_version'] = str(sys.version)
    benchmark.extra_info['python_api'] = str(sys.api_version)
    benchmark.extra_info['kivy_platform'] = platform
    benchmark.extra_info['kivy_version'] = kivy.__version__
    benchmark.extra_info['gl_vendor'] = str(glGetString(GL_VENDOR))
    benchmark.extra_info['gl_renderer'] = str(glGetString(GL_RENDERER))
    benchmark.extra_info['gl_version'] = str(glGetString(GL_VERSION))

    yield benchmark


def test_widget_creation(kivy_benchmark):
    from kivy.uix.widget import Widget
    # create one just so we don't incur loading cost
    w = Widget()
    kivy_benchmark(Widget)


@pytest.mark.parametrize('n', [1, 5, 10, 50, 100, 1_000, 10_000])
def test_widget_empty_draw(kivy_benchmark, n):
    from kivy.graphics import RenderContext
    from kivy.uix.widget import Widget
    ctx = RenderContext()
    root = Widget()
    for x in range(n):
        root.add_widget(Widget())
    ctx.add(root.canvas)

    kivy_benchmark(ctx.draw)


@pytest.mark.parametrize('n', [1, 5, 10, 50, 100, 1_000])
def test_widget_dispatch_touch(kivy_benchmark, n):
    from kivy.tests.common import UnitTestTouch
    from kivy.uix.widget import Widget

    root = Widget()
    for x in range(10):
        parent = Widget()
        for y in range(n):
            parent.add_widget(Widget())
        root.add_widget(parent)

    touch = UnitTestTouch(10, 10)

    def dispatch():
        root.dispatch('on_touch_down', touch)
        root.dispatch('on_touch_move', touch)
        root.dispatch('on_touch_up', touch)

    kivy_benchmark(dispatch)


@pytest.mark.parametrize('n', [1, 5, 10, 50, 100, 1_000])
@pytest.mark.parametrize('name', ['label', 'button'])
@pytest.mark.parametrize('tick', ['tick', 'no_tick'])
def test_random_label_create(kivy_benchmark, n, name, tick):
    from kivy.clock import Clock
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    label = Label(text='*&^%')
    button = Button(text='*&^%')
    cls = Label if name == 'label' else Button

    labels = []
    k = len(ascii_letters)
    for x in range(n):
        label = [ascii_letters[randint(0, k - 1)] for _ in range(10)]
        labels.append(''.join(label))

    def make_labels():
        o = []
        for text in labels:
            o.append(cls(text=text))

        if tick == 'tick':
            Clock.tick()
    kivy_benchmark(make_labels)

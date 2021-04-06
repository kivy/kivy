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
    from kivy.context import Context
    from kivy.clock import ClockBase
    from kivy.factory import FactoryBase, Factory
    from kivy.lang.builder import BuilderBase, Builder

    context = Context(init=False)
    context['Clock'] = ClockBase()
    context['Factory'] = FactoryBase.create_from(Factory)
    context['Builder'] = BuilderBase.create_from(Builder)

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

    context.push()
    try:
        yield benchmark
    finally:
        context.pop()


def test_event_dispatcher_creation(kivy_benchmark):
    from kivy.event import EventDispatcher

    class Event(EventDispatcher):
        pass
    # create one just so we don't incur loading cost
    e = Event()
    kivy_benchmark(Event)


def test_widget_creation(kivy_benchmark):
    from kivy.uix.widget import Widget
    # create one just so we don't incur loading cost
    w = Widget()
    kivy_benchmark(Widget)


def test_kv_widget_creation(kivy_benchmark):
    from kivy.lang import Builder
    from kivy.uix.widget import Widget

    class MyWidget(Widget):
        pass

    Builder.load_string("""
<MyWidget>:
    width: 55
    height: 37
    x: self.width + 5
    y: self.height + 32
""")

    # create one just so we don't incur loading cost
    w = MyWidget()
    kivy_benchmark(MyWidget)


@pytest.mark.parametrize('test_component', ['create', 'set'])
def test_complex_kv_widget(kivy_benchmark, test_component):
    from kivy.lang import Builder
    from kivy.uix.widget import Widget

    class MyWidget(Widget):
        pass

    Builder.load_string("""
<MyWidget>:
    width: 1
    height: '{}dp'.format(self.width + 1)
    x: self.height + 1
    y: self.x + 1
    size_hint_min: self.size_hint
    size_hint_max_y: self.size_hint_min_y
    size_hint_max_x: self.size_hint_min_x
    opacity: sum(self.size_hint_min) + sum(self.size_hint_max)
""")

    # create one just so we don't incur loading cost
    widget = MyWidget()
    w = 0
    sh = 0

    def set_value():
        nonlocal w, sh
        w += 1
        sh += 1
        widget.width = w
        widget.size_hint = sh, sh

    if test_component == 'create':
        kivy_benchmark(MyWidget)
    else:
        kivy_benchmark(set_value)


def get_event_class(name, args, kwargs):
    from kivy.event import EventDispatcher
    import kivy.properties
    from kivy.properties import BooleanProperty, ReferenceListProperty, \
        AliasProperty

    if name == 'AliasProperty':
        class Event(EventDispatcher):
            def get_a(self):
                return 0

            def set_a(self, value):
                pass
            a = AliasProperty(get_a, set_a)

    elif name == 'ReferenceListProperty':
        class Event(EventDispatcher):

            a1 = BooleanProperty(0)
            a2 = BooleanProperty(0)
            a = ReferenceListProperty(a1, a2)

    else:
        cls = getattr(kivy.properties, name)

        class Event(EventDispatcher):

            a = cls(*args, **kwargs)

    return Event


@pytest.mark.parametrize('name,args,kwargs', [
    ('NumericProperty', (0,), {}),
    ('ObjectProperty', (None,), {}),
    ('VariableListProperty', ([0, 0, 0, 0],), {}),
    ('BoundedNumericProperty', (1, ), {'min': 0, 'max': 2}),
    ('DictProperty', ({}, ), {}),
    ('ColorProperty', ([1, 1, 1, 1],), {}),
    ('BooleanProperty', (False,), {}),
    ('OptionProperty', ('a',), {'options': ['a', 'b']}),
    ('StringProperty', ('',), {}),
    ('ListProperty', ([],), {}),
    ('AliasProperty', (), {}),
    ('ReferenceListProperty', (), {}),
])
def test_property_creation(kivy_benchmark, name, args, kwargs):
    event_cls = get_event_class(name, args, kwargs)

    # create one just so we don't incur loading cost
    e = event_cls()
    kivy_benchmark(event_cls)


@pytest.mark.parametrize('name,args,kwargs,val,reset_val', [
    ('NumericProperty', (0,), {}, 10, 0),
    ('NumericProperty', (0,), {}, '10dp', 0),
    ('NumericProperty', (0,), {}, [10, 'dp'], 0),
    ('ObjectProperty', (None,), {}, 5, 0),
    ('VariableListProperty', ([0, 0, 0, 0],), {}, [2, 4], [0]),
    ('BoundedNumericProperty', (1, ), {'min': 0, 'max': 2}, .5, 1),
    ('DictProperty', ({}, ), {}, {'name': 1}, {}),
    ('ColorProperty', ([1, 1, 1, 1],), {}, 'red', [1, 1, 1, 1]),
    ('BooleanProperty', (False,), {}, True, False),
    ('OptionProperty', ('a',), {'options': ['a', 'b']}, 'b', 'a'),
    ('StringProperty', ('',), {}, 'a', ''),
    ('ListProperty', ([],), {}, [1, 2], []),
    ('AliasProperty', (0,), {}, 1, 0),
    ('ReferenceListProperty', ((1, 2),), {}, (3, 4), (1, 2)),
])
@pytest.mark.parametrize('exclude_first', [True, False])
def test_property_set(
        kivy_benchmark, name, args, kwargs, val, reset_val, exclude_first):
    event_cls = get_event_class(name, args, kwargs)

    # create one just so we don't incur loading cost
    e = event_cls()

    def set_property():
        e.a = reset_val
        e.a = val

    if exclude_first:
        set_property()
    kivy_benchmark(set_property)


@pytest.mark.parametrize('n', [1, 10, 100, 1_000])
def test_widget_empty_draw(kivy_benchmark, n):
    from kivy.graphics import RenderContext
    from kivy.uix.widget import Widget
    ctx = RenderContext()
    root = Widget()
    for x in range(n):
        root.add_widget(Widget())
    ctx.add(root.canvas)

    kivy_benchmark(ctx.draw)


@pytest.mark.parametrize('n', [1, 10, 100, 1_000])
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


@pytest.mark.parametrize('n', [1, 10, 100, 1_000])
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


def test_parse_kv(kivy_benchmark):
    from kivy.lang import Builder
    suffix = 0

    def parse_kv():
        nonlocal suffix
        Builder.load_string(f"""
<MyWidget{suffix}>:
    width: 55
    height: 37
    x: self.width + 5
    y: self.height + 32
""")
        suffix += 1

    # create one just so we don't incur loading cost
    parse_kv()
    kivy_benchmark(parse_kv)

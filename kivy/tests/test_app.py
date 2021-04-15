from os import name
import os.path
from math import isclose
from textwrap import dedent

from kivy.app import App
from kivy.clock import Clock
from kivy import lang
from kivy.tests import GraphicUnitTest, async_run, UnitKivyApp


class AppTest(GraphicUnitTest):
    def test_start_raw_app(self):
        lang._delayed_start = None
        a = App()
        Clock.schedule_once(a.stop, .1)
        a.run()

    def test_start_app_with_kv(self):
        class TestKvApp(App):
            pass

        lang._delayed_start = None
        a = TestKvApp()
        Clock.schedule_once(a.stop, .1)
        a.run()

    def test_user_data_dir(self):
        a = App()
        data_dir = a.user_data_dir
        assert os.path.exists(data_dir)

    def test_directory(self):
        a = App()
        assert os.path.exists(a.directory)

    def test_name(self):
        class NameTest(App):
            pass

        a = NameTest()
        assert a.name == 'nametest'


def basic_app():
    from kivy.app import App
    from kivy.uix.label import Label

    class TestApp(UnitKivyApp, App):
        def build(self):
            return Label(text='Hello, World!')

    return TestApp()


@async_run(app_cls_func=basic_app)
async def test_basic_app(kivy_app):
    assert kivy_app.root.text == 'Hello, World!'


def button_app():
    from kivy.app import App
    from kivy.uix.togglebutton import ToggleButton

    class TestApp(UnitKivyApp, App):
        def build(self):
            return ToggleButton(text='Hello, World!')

    return TestApp()


@async_run(app_cls_func=button_app)
async def test_button_app(kivy_app):
    assert kivy_app.root.text == 'Hello, World!'
    assert kivy_app.root.state == 'normal'

    async for state, touch_pos in kivy_app.do_touch_down_up(
            widget=kivy_app.root, widget_jitter=True):
        pass

    assert kivy_app.root.state == 'down'


def scatter_app():
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scatter import Scatter

    class TestApp(UnitKivyApp, App):
        def build(self):
            label = Label(text='Hello, World!', size=('200dp', '200dp'))
            scatter = Scatter(do_scale=False, do_rotation=False)
            scatter.add_widget(label)
            return scatter

    return TestApp()


@async_run(app_cls_func=scatter_app)
async def test_drag_app(kivy_app):
    scatter = kivy_app.root
    assert tuple(scatter.pos) == (0, 0)

    async for state, touch_pos in kivy_app.do_touch_drag(
            pos=(100, 100), target_pos=(200, 200)):
        pass

    assert isclose(scatter.x, 100)
    assert isclose(scatter.y, 100)


def text_app():
    from kivy.app import App
    from kivy.uix.textinput import TextInput

    class TestApp(UnitKivyApp, App):
        def build(self):
            return TextInput()

    return TestApp()


@async_run(app_cls_func=text_app)
async def test_text_app(kivy_app):
    text = kivy_app.root
    assert text.text == ''

    # activate widget
    async for state, touch_pos in kivy_app.do_touch_down_up(widget=text):
        pass

    async for state, value in kivy_app.do_keyboard_key(key='A', num_press=4):
        pass
    async for state, value in kivy_app.do_keyboard_key(key='q', num_press=3):
        pass

    assert text.text == 'AAAAqqq'


def graphics_app():
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, Rectangle

    class TestApp(UnitKivyApp, App):
        def build(self):
            widget = Widget()
            with widget.canvas:
                Color(1, 0, 0, 1)
                Rectangle(pos=(0, 0), size=(100, 100))
                Color(0, 1, 0, 1)
                Rectangle(pos=(100, 0), size=(100, 100))
            return widget

    return TestApp()


@async_run(app_cls_func=graphics_app)
async def test_graphics_app(kivy_app):
    widget = kivy_app.root
    (r1, g1, b1, a1), (r2, g2, b2, a2) = kivy_app.get_widget_pos_pixel(
        widget, [(50, 50), (150, 50)])

    assert not g1 and not b1 and not r2 and not b2
    assert r1 > 50 and a1 > 50 and g2 > 50 and a2 > 50


def kv_app_ref_app():
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.properties import ObjectProperty
    from kivy.uix.widget import Widget

    class MyWidget(Widget):

        obj = ObjectProperty(None)

    Builder.load_string(dedent(
        """
        <MyWidget>:
            obj: app.__self__
        """))

    class TestApp(UnitKivyApp, App):
        def build(self):
            return MyWidget()

    return TestApp()


@async_run(app_cls_func=kv_app_ref_app)
async def test_leak_app_kv_property(kivy_app):
    # just tests whether the app is gc'd after the test is complete
    pass


def kv_app_default_ref_app():
    from kivy.app import App
    from kivy.lang import Builder

    class TestApp(UnitKivyApp, App):
        def build(self):
            # create property in kv and set app to it
            return Builder.load_string(dedent(
                """
                Widget:
                    obj: app.__self__
                """))

    return TestApp()


@async_run(app_cls_func=kv_app_default_ref_app)
async def test_leak_app_default_kv_property(kivy_app):
    # just tests whether the app is gc'd after the test is complete
    pass

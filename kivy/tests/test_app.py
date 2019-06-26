import os.path

from kivy.app import App
from kivy.clock import Clock
from kivy import lang
from kivy.tests import GraphicUnitTest, async_run, async_sleep, UnitKivyApp


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
        if not os.path.exists(data_dir):
            raise Exception("user_data_dir didnt exists")


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

    async for touch_pos, state in kivy_app.do_touch_down_up(
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

    async for touch_pos, state in kivy_app.do_touch_drag(
            pos=(100, 100), target_pos=(200, 200)):
        pass

    assert tuple(scatter.pos) == (100, 100)

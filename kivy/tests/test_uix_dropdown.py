from kivy.tests import async_run, UnitKivyApp


def dropdown_app():
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.dropdown import DropDown
    from kivy.uix.label import Label

    class RootButton(Button):

        dropdown = None

        def on_touch_down(self, touch):
            assert self.dropdown.attach_to is None
            return super(RootButton, self).on_touch_down(touch)

        def on_touch_move(self, touch):
            assert self.dropdown.attach_to is None
            return super(RootButton, self).on_touch_move(touch)

        def on_touch_up(self, touch):
            assert self.dropdown.attach_to is None
            return super(RootButton, self).on_touch_up(touch)

    class TestApp(UnitKivyApp, App):
        def build(self):
            root = RootButton(text='Root')
            self.attach_widget = Label(text='Attached widget')
            root.add_widget(self.attach_widget)

            root.dropdown = self.dropdown = DropDown(
                auto_dismiss=True, min_state_time=0)
            self.inner_widget = w = Label(
                size_hint=(None, None), text='Dropdown')
            root.dropdown.add_widget(w)
            return root

    return TestApp()


@async_run(app_cls_func=dropdown_app)
async def test_dropdown_app(kivy_app):
    await kivy_app.wait_clock_frames(2)
    dropdown = kivy_app.dropdown
    button = kivy_app.root
    assert dropdown.attach_to is None

    kivy_app.attach_widget.size = button.width * 3 / 5, 2
    kivy_app.attach_widget.top = button.height
    kivy_app.inner_widget.size = button.width * 3 / 5, button.height

    # just press button
    async for _ in kivy_app.do_touch_down_up(widget=button):
        pass
    async for _ in kivy_app.do_touch_drag(widget=button, dx=button.width / 4):
        pass

    # open dropdown
    dropdown.open(kivy_app.attach_widget)
    dropdown.pos = 0, 0
    await kivy_app.wait_clock_frames(2)
    assert dropdown.attach_to is not None

    # press within dropdown area - should stay open
    async for _ in kivy_app.do_touch_down_up(widget=button):
        pass
    assert dropdown.attach_to is not None
    # start in dropdown but release outside - should stay open
    async for _ in kivy_app.do_touch_drag(widget=button, dx=button.width / 4):
        pass
    assert dropdown.attach_to is not None

    # start outside but release in dropdown - should close
    async for _ in kivy_app.do_touch_drag(
            pos=(button.center_x + button.width / 4, button.center_y),
            target_widget=button):
        pass
    assert dropdown.attach_to is None

    # open dropdown again
    dropdown.open(kivy_app.attach_widget)
    dropdown.pos = 0, 0
    await kivy_app.wait_clock_frames(2)
    assert dropdown.attach_to is not None

    # press outside dropdown area to close it - should close
    async for _ in kivy_app.do_touch_down_up(
            pos=(button.center_x + button.width / 4, button.center_y)):
        pass
    assert dropdown.attach_to is None

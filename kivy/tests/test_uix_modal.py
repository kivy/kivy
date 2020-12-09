from kivy.tests import async_run, UnitKivyApp
from math import isclose


def modal_app():
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.modalview import ModalView

    class ModalButton(Button):

        modal = None

        def on_touch_down(self, touch):
            assert self.modal._window is None
            return super(ModalButton, self).on_touch_down(touch)

        def on_touch_move(self, touch):
            assert self.modal._window is None
            return super(ModalButton, self).on_touch_move(touch)

        def on_touch_up(self, touch):
            assert self.modal._window is None
            return super(ModalButton, self).on_touch_up(touch)

    class TestApp(UnitKivyApp, App):
        def build(self):
            root = ModalButton()
            root.modal = self.modal_view = ModalView(
                size_hint=(.2, .5), auto_dismiss=True)
            return root

    return TestApp()


@async_run(app_cls_func=modal_app)
async def test_modal_app(kivy_app):
    await kivy_app.wait_clock_frames(2)
    modal = kivy_app.modal_view
    button = kivy_app.root
    modal._anim_duration = 0
    assert modal._window is None

    # just press button
    async for _ in kivy_app.do_touch_down_up(widget=button):
        pass
    async for _ in kivy_app.do_touch_drag(widget=button, dx=button.width / 4):
        pass

    # open modal
    modal.open()
    await kivy_app.wait_clock_frames(2)
    assert modal._window is not None
    assert isclose(modal.center_x, button.center_x, abs_tol=.1)
    assert isclose(modal.center_y, button.center_y, abs_tol=.1)

    # press within modal area - should stay open
    async for _ in kivy_app.do_touch_down_up(widget=button):
        pass
    assert modal._window is not None
    # start in modal but release outside - should stay open
    async for _ in kivy_app.do_touch_drag(widget=button, dx=button.width / 4):
        pass
    assert modal._window is not None

    # start outside but release in modal - should close
    async for _ in kivy_app.do_touch_drag(
            pos=(button.center_x + button.width / 4, button.center_y),
            target_widget=button):
        pass
    assert modal._window is None

    # open modal again
    modal.open()
    await kivy_app.wait_clock_frames(2)
    assert modal._window is not None

    # press outside modal area - should close
    async for _ in kivy_app.do_touch_down_up(
            pos=(button.center_x + button.width / 4, button.center_y)):
        pass
    assert modal._window is None

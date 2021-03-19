""" modal view unit tests. """
from kivy.tests import async_run, UnitKivyApp
from math import isclose


def modal_app():
    """ test app factory function. """
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.modalview import ModalView

    # noinspection PyProtectedMember
    class ModalButton(Button):
        """ button used as root widget to test touch. """
        modal = None

        def on_touch_down(self, touch):
            """ touch down event handler. """
            assert not self.modal._is_open
            return super(ModalButton, self).on_touch_down(touch)

        def on_touch_move(self, touch):
            """ touch move event handler. """
            assert not self.modal._is_open
            return super(ModalButton, self).on_touch_move(touch)

        def on_touch_up(self, touch):
            """ touch up event handler. """
            assert not self.modal._is_open
            return super(ModalButton, self).on_touch_up(touch)

    class TestApp(UnitKivyApp, App):
        """ test app class. """
        def build(self):
            """ build root layout. """
            root = ModalButton()
            root.modal = ModalView(size_hint=(.2, .5))
            return root

    return TestApp()


@async_run(app_cls_func=modal_app)
async def test_modal_app(kivy_app):
    await kivy_app.wait_clock_frames(2)
    button = kivy_app.root
    modal = button.modal
    modal._anim_duration = 0
    assert not modal._is_open

    # just press button
    async for _ in kivy_app.do_touch_down_up(widget=button):
        assert not modal._is_open
    async for _ in kivy_app.do_touch_drag(widget=button, dx=button.width / 4):
        assert not modal._is_open

    # open modal
    modal.open()
    await kivy_app.wait_clock_frames(2)
    assert modal._is_open
    assert isclose(modal.center_x, button.center_x, abs_tol=.1)
    assert isclose(modal.center_y, button.center_y, abs_tol=.1)

    # press within modal area - should stay open
    async for _ in kivy_app.do_touch_down_up(widget=button):
        pass
    assert modal._is_open
    # start in modal but release outside - should stay open
    async for _ in kivy_app.do_touch_drag(widget=button, dx=button.width / 4):
        pass
    assert modal._is_open

    # start outside but release in modal - should close
    async for _ in kivy_app.do_touch_drag(
            pos=(button.center_x + button.width / 4, button.center_y),
            target_widget=button):
        pass
    assert not modal._is_open

    # open modal again
    modal.open()
    await kivy_app.wait_clock_frames(2)
    assert modal._is_open

    # press outside modal area - should close
    async for _ in kivy_app.do_touch_down_up(
            pos=(button.center_x + button.width / 4, button.center_y)):
        pass
    assert not modal._is_open

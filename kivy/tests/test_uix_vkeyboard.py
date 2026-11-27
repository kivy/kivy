import pytest


@pytest.fixture
def vkeyboard(kivy_clock):
    from kivy.uix.vkeyboard import VKeyboard
    keyboard = VKeyboard(size=(400, 200))
    kivy_clock.tick()
    return keyboard


def test_draw_keys_with_the_enabled_background(vkeyboard):
    vkeyboard.draw_keys()
    assert vkeyboard.children


def test_draw_keys_when_disabled_uses_the_disabled_key_background(vkeyboard):
    # The disabled branch referred to a property that does not exist, so
    # drawing a disabled keyboard raised AttributeError.
    vkeyboard.disabled = True
    vkeyboard.draw_keys()
    assert vkeyboard.children

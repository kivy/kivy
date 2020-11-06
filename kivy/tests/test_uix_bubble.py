import pytest


@pytest.mark.parametrize('prop_name', (
    '_fills_row_first',
    '_fills_from_left_to_right',
    '_fills_from_top_to_bottom',
))
def test_a_certain_properties_exist_in_any_of_the_super_classes(prop_name):
    from kivy.uix.bubble import Bubble
    super_classes = Bubble.mro()[1:]  # exclude Bubble itself
    assert any(hasattr(klass, prop_name) for klass in super_classes)


@pytest.mark.parametrize('orientation', ('vertical', 'horizontal'))
def test_always_lr_tb(orientation):
    from kivy.uix.bubble import Bubble
    b = Bubble(orientation=orientation)
    assert b._fills_row_first
    assert b._fills_from_left_to_right
    assert b._fills_from_top_to_bottom

import pytest


@pytest.mark.parametrize('prop_name', (
    '_fills_row_first',
    '_fills_from_left_to_right',
    '_fills_from_top_to_bottom',
))
def test_a_certain_properties_from_the_super_class_are_overwritten(prop_name):
    from kivy.uix.bubble import Bubble
    from kivy.uix.gridlayout import GridLayout
    assert issubclass(Bubble, GridLayout)
    assert getattr(Bubble, prop_name) is not getattr(GridLayout, prop_name)


@pytest.mark.parametrize('orientation', ('vertical', 'horizontal'))
def test_always_lr_tb(orientation):
    from kivy.uix.bubble import Bubble
    b = Bubble(orientation=orientation)
    assert b._fills_row_first
    assert b._fills_from_left_to_right
    assert b._fills_from_top_to_bottom

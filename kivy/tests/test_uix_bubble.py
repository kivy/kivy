import pytest


@pytest.mark.parametrize('prop_name', (
    '_fills_row_first',
    '_fills_from_left_to_right',
    '_fills_from_top_to_bottom',
))
def test_a_certain_properties_exist_in_the_super_class(prop_name):
    from kivy.uix.gridlayout import GridLayout
    assert hasattr(GridLayout, prop_name)


@pytest.mark.parametrize('orientation', ('vertical', 'horizontal'))
def test_always_lr_tb(orientation):
    from kivy.uix.bubble import Bubble
    b = Bubble(orientation=orientation)
    assert b._fills_row_first
    assert b._fills_from_left_to_right
    assert b._fills_from_top_to_bottom

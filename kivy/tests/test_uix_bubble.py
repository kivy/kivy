import pytest


@pytest.mark.parametrize('orientation', ('vertical', 'horizontal'))
def test_always_lr_tb(orientation):
    from kivy.uix.bubble import Bubble
    b = Bubble(orientation=orientation)
    assert b._fills_row_first
    assert b._fills_from_left_to_right
    assert b._fills_from_top_to_bottom

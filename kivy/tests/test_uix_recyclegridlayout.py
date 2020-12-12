import pytest


@pytest.mark.parametrize('orientation, tl, tr, bl, br', (
    ('lr-tb', 0, 1, 2, 3, ),
    ('lr-bt', 2, 3, 0, 1, ),
    ('rl-tb', 1, 0, 3, 2, ),
    ('rl-bt', 3, 2, 1, 0, ),
    ('tb-lr', 0, 2, 1, 3, ),
    ('tb-rl', 2, 0, 3, 1, ),
    ('bt-lr', 1, 3, 0, 2, ),
    ('bt-rl', 3, 1, 2, 0, ),
))
def test_reorder_view_indices(orientation, tl, tr, bl, br):
    '''test a certain part of `RecycleGridLayout.compute_visible_views()`'''
    fills_row_first = orientation[0] in 'rl'
    fills_from_left_to_right = 'lr' in orientation
    fills_from_top_to_bottom = 'tb' in orientation

    cond1 = not fills_from_top_to_bottom
    cond2 = not fills_from_left_to_right
    if not fills_row_first:
        tr, bl = bl, tr
        cond1, cond2 = cond2, cond1
    if cond1:
        tl, tr, bl, br = bl, br, tl, tr
    if cond2:
        tl, tr, bl, br = tr, tl, br, bl

    assert (tl, tr, bl, br, ) == (0, 1, 2, 3, )

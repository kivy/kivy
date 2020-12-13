import pytest


@pytest.mark.parametrize('orientation, input, expected_output', (
    # A situation where both of a number of columns and a number of rows are
    # greater than 1. In this situation, the 'expected_output' is in ascending
    # order.
    #
    # |----|----|
    # |    |    |
    # |----|----|  2x2
    # |    |    |
    # |----|----|
    #
    ('lr-tb', (0, 1, 2, 3, ), (0, 1, 2, 3, ), ),
    ('lr-bt', (2, 3, 0, 1, ), (0, 1, 2, 3, ), ),
    ('rl-tb', (1, 0, 3, 2, ), (0, 1, 2, 3, ), ),
    ('rl-bt', (3, 2, 1, 0, ), (0, 1, 2, 3, ), ),
    ('tb-lr', (0, 2, 1, 3, ), (0, 1, 2, 3, ), ),
    ('tb-rl', (2, 0, 3, 1, ), (0, 1, 2, 3, ), ),
    ('bt-lr', (1, 3, 0, 2, ), (0, 1, 2, 3, ), ),
    ('bt-rl', (3, 1, 2, 0, ), (0, 1, 2, 3, ), ),

    # A situation where either of a number of columns or a number of rows is
    # 1, which is the situation of GitHub issue #7255. In this situation, we
    # cannot just sort in ascending order depending on the orientation.
    #
    # |----|----|----|
    # |    |    |    |  3x1
    # |----|----|----|
    #
    ('lr-tb', (0, 2, 0, 2, ), (0, 2, 0, 2, ), ),
    ('lr-bt', (0, 2, 0, 2, ), (0, 2, 0, 2, ), ),
    ('rl-tb', (2, 0, 2, 0, ), (0, 2, 0, 2, ), ),
    ('rl-bt', (2, 0, 2, 0, ), (0, 2, 0, 2, ), ),
    ('tb-lr', (0, 2, 0, 2, ), (0, 0, 2, 2, ), ),
    ('tb-rl', (2, 0, 2, 0, ), (0, 0, 2, 2, ), ),
    ('bt-lr', (0, 2, 0, 2, ), (0, 0, 2, 2, ), ),
    ('bt-rl', (2, 0, 2, 0, ), (0, 0, 2, 2, ), ),
    #
    # |----|
    # |    |
    # |----|
    # |    |  1x3
    # |----|
    # |    |
    # |----|
    #
    ('lr-tb', (0, 0, 2, 2, ), (0, 0, 2, 2, ), ),
    ('lr-bt', (2, 2, 0, 0, ), (0, 0, 2, 2, ), ),
    ('rl-tb', (0, 0, 2, 2, ), (0, 0, 2, 2, ), ),
    ('rl-bt', (2, 2, 0, 0, ), (0, 0, 2, 2, ), ),
    ('tb-lr', (0, 0, 2, 2, ), (0, 2, 0, 2, ), ),
    ('tb-rl', (0, 0, 2, 2, ), (0, 2, 0, 2, ), ),
    ('bt-lr', (2, 2, 0, 0, ), (0, 2, 0, 2, ), ),
    ('bt-rl', (2, 2, 0, 0, ), (0, 2, 0, 2, ), ),
))
def test_reorder_view_indices(orientation, input, expected_output):
    '''test a certain part of `RecycleGridLayout.compute_visible_views()`'''
    fills_row_first = orientation[0] in 'rl'
    fills_from_left_to_right = 'lr' in orientation
    fills_from_top_to_bottom = 'tb' in orientation
    tl, tr, bl, br = input

    cond1 = not fills_from_top_to_bottom
    cond2 = not fills_from_left_to_right
    if not fills_row_first:
        tr, bl = bl, tr
        cond1, cond2 = cond2, cond1
    if cond1:
        tl, tr, bl, br = bl, br, tl, tr
    if cond2:
        tl, tr, bl, br = tr, tl, br, bl

    assert (tl, tr, bl, br, ) == expected_output

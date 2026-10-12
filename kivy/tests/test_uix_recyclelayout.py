import pytest


KV = '''
RecycleView:
    viewclass: 'Widget'
    size: 300, 300
    data: ({{}} for __ in range(20))
    RecycleBoxLayout:
        id: layout
        orientation: '{orientation}'
        size_hint: {layout_hint}
        {extent}: self.minimum_{extent}
        default_size: {default_size}
        default_size_hint: {default_hint}
'''

VERTICAL = dict(
    orientation='vertical', layout_hint='(1, None)', extent='height',
    default_size='(None, 30)', default_hint='(1, None)')
HORIZONTAL = dict(
    orientation='horizontal', layout_hint='(None, 1)', extent='width',
    default_size='(30, None)', default_hint='(None, 1)')


def build_rv(params):
    from kivy.lang import Builder
    return Builder.load_string(KV.format(**params))


def view_map(layout):
    return {view: idx for view, idx in layout.view_indices.items()}


@pytest.mark.parametrize(
    "params, axis", [(VERTICAL, 'width'), (HORIZONTAL, 'height')])
def test_resize_along_non_layout_axis_keeps_view_mapping(
        kivy_clock, params, axis):
    '''Resizing along the axis the layout does not control must not change
    which view shows which index.
    '''
    rv = build_rv(params)
    kivy_clock.tick()
    layout = rv.ids.layout
    before = view_map(layout)
    assert before

    for i in range(4):
        setattr(rv, axis, 300 + 20 * (i + 1))
        kivy_clock.tick()
        assert view_map(layout) == before


def test_invalidate_keeps_view_to_index_assignment(kivy_clock):
    '''After the layout is recomputed, each index must get back the view it
    showed before, not the view of the mirrored index.
    '''
    rv = build_rv(VERTICAL)
    kivy_clock.tick()
    layout = rv.ids.layout
    before = view_map(layout)

    rv.refresh_from_layout()
    kivy_clock.tick()

    assert view_map(layout) == before

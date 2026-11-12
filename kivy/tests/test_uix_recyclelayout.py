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


@pytest.mark.parametrize(
    'params, axis, dimension', [(VERTICAL, 'width', 'cols'),
                                (HORIZONTAL, 'height', 'rows')])
def test_grid_resize_along_non_layout_axis_keeps_view_mapping(
        kivy_clock, params, axis, dimension):
    from kivy.lang import Builder
    grid_kv = KV.replace(
        'RecycleBoxLayout:', 'RecycleGridLayout:\n        ' + dimension + ': 1')
    rv = Builder.load_string(grid_kv.format(**dict(params, orientation='lr-tb')))
    kivy_clock.tick()
    layout = rv.ids.layout
    before = view_map(layout)
    assert before

    for i in range(4):
        size = 300 + 20 * (i + 1)
        setattr(rv, axis, size)
        kivy_clock.tick()
        # Grid extent changes schedule another layout pass.
        kivy_clock.tick()
        assert view_map(layout) == before
        assert all(getattr(view, axis) == size for view in before)


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


@pytest.mark.parametrize(
    'params, axis, scroll', [(VERTICAL, 'width', 'scroll_y'),
                             (HORIZONTAL, 'height', 'scroll_x')])
def test_scroll_then_resize_keeps_visible_views(kivy_clock, params, axis, scroll):
    rv = build_rv(params)
    kivy_clock.tick()
    setattr(rv, scroll, .5)
    kivy_clock.tick()
    layout = rv.ids.layout
    before = view_map(layout)
    assert before and rv.view_adapter.dirty_views
    for size in (340, 280, 360):
        setattr(rv, axis, size)
        kivy_clock.tick()
        assert view_map(layout) == before
        assert all(getattr(view, axis) == size for view in before)


@pytest.mark.parametrize('indices', [[1, 2], [2, 1], [1, 4, 2]])
@pytest.mark.parametrize('mixed', [False, True])
def test_dirty_views_reserved_before_recycling(indices, mixed, monkeypatch):
    from kivy.uix.recycleview.views import RecycleDataAdapter
    from kivy.uix.label import Label
    from kivy.uix.widget import Widget
    from collections import defaultdict
    import kivy.uix.recycleview.views as views
    monkeypatch.setattr(views, '_cached_views', defaultdict(list))
    monkeypatch.setattr(views, '_cache_count', 0)
    adapter = RecycleDataAdapter()
    classes = [{'viewclass': Label if mixed and i % 2 else Widget}
               for i in range(6)]
    data = [{} for _ in classes]
    adapter.set_visible_views([2, 3], data, classes)
    original = adapter.views.copy()
    adapter.make_views_dirty()
    adapter.set_visible_views(indices, data, classes)
    assert adapter.views[2] is original[2]
    assert len(set(adapter.views.values())) == len(adapter.views)
    assert all(type(v) is classes[i]['viewclass']
               for i, v in adapter.views.items())


def test_data_invalidation_does_not_reserve_stale_views():
    from kivy.uix.recycleview.views import RecycleDataAdapter
    from kivy.uix.label import Label
    adapter = RecycleDataAdapter()
    classes = [{'viewclass': Label}] * 4
    adapter.set_visible_views([0, 1], [{'text': str(i)} for i in range(4)], classes)
    adapter.make_views_dirty()
    adapter.invalidate()
    assert not adapter.views and not adapter.dirty_views
    adapter.set_visible_views([0, 1], [{'text': 'new'}] * 4, classes)
    assert all(v.text == 'new' for v in adapter.views.values())


@pytest.mark.parametrize('operation', ['refresh', 'insert', 'remove', 'replace'])
def test_data_changes_refresh_values_and_classes(kivy_clock, operation):
    from kivy.lang import Builder
    rv = Builder.load_string('''
RecycleView:
    size_hint: None, None
    size: 300, 300
    RecycleBoxLayout:
        id: layout
        key_viewclass: 'kind'
        orientation: 'vertical'
        size_hint: 1, None
        height: self.minimum_height
        default_size: None, 30
        default_size_hint: 1, None
''')
    rv.data = [dict(kind='Label' if i % 2 else 'Button', text=str(i))
               for i in range(30)]
    kivy_clock.tick()
    rv.scroll_y = .5
    kivy_clock.tick()
    if operation == 'refresh':
        rv.data[7]['text'] = 'changed'
        rv.refresh_from_data()
    elif operation == 'insert':
        rv.data.insert(0, dict(kind='Label', text='inserted'))
    elif operation == 'remove':
        del rv.data[0:4]
    else:
        rv.data[7] = dict(kind='Button', text='replacement')
    kivy_clock.tick()
    rv.width = 340
    kivy_clock.tick()
    from kivy.factory import Factory
    for view, index in rv.ids.layout.view_indices.items():
        assert view.text == rv.data[index]['text']
        assert type(view) is getattr(Factory, rv.data[index]['kind'])
        assert view.width == 340


def test_layout_focus_and_selection_survive_layout_only_resize(kivy_clock):
    from kivy.uix.behaviors import FocusBehavior
    from kivy.uix.recycleview.layout import LayoutSelectionBehavior
    from kivy.uix.recycleboxlayout import RecycleBoxLayout
    from kivy.uix.recycleview.views import RecycleDataViewBehavior
    from kivy.uix.label import Label
    from kivy.uix.recycleview import RecycleView
    from kivy.properties import BooleanProperty

    class SelectableLayout(FocusBehavior, LayoutSelectionBehavior,
                           RecycleBoxLayout):
        pass

    class Row(RecycleDataViewBehavior, Label):
        selected = BooleanProperty(False)

        def apply_selection(self, rv, index, is_selected):
            self.selected = is_selected

    rv = RecycleView(size_hint=(None, None), size=(300, 300))
    layout = SelectableLayout(viewclass=Row, orientation='vertical',
                              size_hint=(1, None), default_size=(None, 30),
                              default_size_hint=(1, None))
    layout.bind(minimum_height=layout.setter('height'))
    rv.add_widget(layout)
    rv.data = [{'text': str(i)} for i in range(20)]
    kivy_clock.tick()
    rv.scroll_y = .5
    kivy_clock.tick()
    layout.select_node(7)
    layout.focus = True
    before = rv.view_adapter.views[7]
    assert before.selected and layout.focus
    rv.width = 340
    kivy_clock.tick()
    assert layout.focus and layout.selected_nodes == [7]
    assert rv.view_adapter.views[7] is before
    assert before.selected
    assert all(v.selected == (i == 7) for i, v in rv.view_adapter.views.items())
    layout.focus = False


def test_relayout_with_partially_overlapping_viewport(kivy_clock):
    rv = build_rv(VERTICAL)
    kivy_clock.tick()
    rv.scroll_y = .5
    kivy_clock.tick()
    before = rv.view_adapter.views.copy()
    # Grow the viewport and change the scroll offset in the same layout pass.
    rv.height = 390
    rv.scroll_y = .7
    kivy_clock.tick()
    after = rv.view_adapter.views
    overlap = before.keys() & after.keys()
    assert overlap and before.keys() != after.keys()
    assert all(after[i] is before[i] for i in overlap)


def test_dirty_reservation_accepts_generator_and_missing_viewclass(monkeypatch):
    from collections import defaultdict
    import kivy.uix.recycleview.views as views
    from kivy.uix.widget import Widget
    monkeypatch.setattr(views, '_cached_views', defaultdict(list))
    monkeypatch.setattr(views, '_cache_count', 0)
    adapter = views.RecycleDataAdapter()
    data = [{}, {}, {}]
    classes = [{'viewclass': Widget}, {'viewclass': None},
               {'viewclass': Widget}]
    adapter.set_visible_views([2], data, classes)
    saved = adapter.views[2]
    adapter.make_views_dirty()
    adapter.set_visible_views((i for i in range(3)), data, classes)
    assert adapter.views[2] is saved
    assert set(adapter.views) == {0, 2}


@pytest.mark.parametrize('suppress_reserved', [False, True])
def test_dirty_reservation_preserves_get_view_override(monkeypatch,
                                                       suppress_reserved):
    from collections import defaultdict
    import kivy.uix.recycleview.views as views
    from kivy.uix.label import Label
    monkeypatch.setattr(views, '_cached_views', defaultdict(list))
    monkeypatch.setattr(views, '_cache_count', 0)

    class Adapter(views.RecycleDataAdapter):
        def get_view(self, index, data_item, viewclass):
            calls.append(index)
            if suppress[0] and index == 2:
                return None
            view = super().get_view(index, data_item, viewclass)
            view.text = 'hook:' + str(index)
            return view

    calls = []
    suppress = [False]
    adapter = Adapter()
    data = [{} for _ in range(5)]
    classes = [{'viewclass': Label}] * len(data)
    adapter.set_visible_views([2, 3], data, classes)
    adapter.make_views_dirty()
    suppress[0] = suppress_reserved
    calls.clear()
    adapter.set_visible_views([1, 2], data, classes)
    assert sorted(calls) == [1, 2]
    if suppress_reserved:
        assert 2 not in adapter.views
    else:
        assert adapter.views[2].text == 'hook:2'


def test_custom_layout_dirty_and_invalidated_lifecycle(kivy_clock):
    from kivy.uix.recycleboxlayout import RecycleBoxLayout
    from kivy.uix.recycleview import RecycleView
    from kivy.uix.widget import Widget

    class Layout(RecycleBoxLayout):
        def clear_layout(self):
            events.append('invalidate')
            return super().clear_layout()

        def remove_views(self):
            events.append('dirty')
            return super().remove_views()

    events = []
    rv = RecycleView(size_hint=(None, None), size=(300, 300))
    layout = Layout(viewclass=Widget, orientation='vertical',
                    size_hint=(1, None), default_size=(None, 30),
                    default_size_hint=(1, None))
    layout.bind(minimum_height=layout.setter('height'))
    rv.add_widget(layout)
    rv.data = [{} for _ in range(20)]
    kivy_clock.tick()
    rv.scroll_y = .5
    kivy_clock.tick()
    events.clear()
    before = rv.view_adapter.views.copy()
    rv.width = 340
    kivy_clock.tick()
    assert 'dirty' in events and 'invalidate' not in events
    assert rv.view_adapter.views == before
    events.clear()
    rv.data[7] = {'opacity': .5}
    kivy_clock.tick()
    assert 'invalidate' in events
    assert rv.view_adapter.views[7].opacity == .5

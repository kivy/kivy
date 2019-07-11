import pytest
import functools

NON_RELATIVE_TYPE_WIDGET_CLS_NAMES = ('Widget', )
RELATIVE_TYPE_WIDGET_CLS_NAMES = (
    'RelativeLayout', 'Scatter', 'ScrollView',
)
ALL_WIDGET_CLS_NAMES = \
    NON_RELATIVE_TYPE_WIDGET_CLS_NAMES + \
    RELATIVE_TYPE_WIDGET_CLS_NAMES


@functools.lru_cache(maxsize=1)
def get_relative_type_widget_classes():
    from kivy.factory import Factory
    return tuple(
        Factory.get(cls_name)
        for cls_name in RELATIVE_TYPE_WIDGET_CLS_NAMES
    )


def is_relative_type(widget):
    return isinstance(widget, get_relative_type_widget_classes())


@pytest.mark.parametrize('widget_cls_name', RELATIVE_TYPE_WIDGET_CLS_NAMES)
def test_to_local_and_to_parent__relative(widget_cls_name):
    from kivy.clock import Clock
    from kivy.factory import Factory
    widget = Factory.get(widget_cls_name)(pos=(100, 100))
    Clock.tick()
    assert widget.to_local(0, 0) == (-100, -100)
    assert widget.to_parent(0, 0) == (100, 100)


@pytest.mark.parametrize('widget_cls_name', NON_RELATIVE_TYPE_WIDGET_CLS_NAMES)
def test_to_local_and_to_parent__not_relative(widget_cls_name):
    from kivy.clock import Clock
    from kivy.factory import Factory
    widget = Factory.get(widget_cls_name)(pos=(100, 100))
    Clock.tick()
    assert widget.to_local(0, 0) == (0, 0)
    assert widget.to_parent(0, 0) == (0, 0)


@pytest.mark.parametrize('root_widget_cls_name', ALL_WIDGET_CLS_NAMES)
@pytest.mark.parametrize('target_widget_cls_name', ALL_WIDGET_CLS_NAMES)
def test_to_window_and_to_widget(root_widget_cls_name, target_widget_cls_name):
    from kivy.clock import Clock
    from textwrap import dedent
    from kivy.lang import Builder
    root = Builder.load_string(dedent('''
        {}:
            pos: 100, 0

            # In case the root widget is ScrollView, this cushion is needed,
            # because ScrollView's direct child is always at pos(0, 0)
            Widget:
                pos: 0, 0

                {}:
                    id: target
                    pos: 0, 100
        ''').format(root_widget_cls_name, target_widget_cls_name))
    Clock.tick()
    target = root.ids.target
    if is_relative_type(root):
        assert target.to_window(*target.pos) == (100, 100)
        assert target.to_widget(0, 0) == \
            ((-100, -100) if is_relative_type(target) else (-100, 0))
    else:
        assert target.to_window(*target.pos) == (0, 100)
        assert target.to_widget(0, 0) == \
            ((0, -100) if is_relative_type(target) else (0, 0))

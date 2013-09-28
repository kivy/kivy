from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.models import SelectableDataItem
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import CompositeListItem
from kivy.uix.listview import ListItemLabel
from kivy.uix.listview import ListView
from kivy.uix.gridlayout import GridLayout


class IntegerDataItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(IntegerDataItem, self).__init__(**kwargs)
        self.x1 = kwargs.get('x1', 1)
        self.x10 = kwargs.get('x1', 10)
        self.x100_text = kwargs.get('x1', '100')


class MainView(GridLayout):
    '''Uses :class:`CompositeListItem` for list item views comprised by two
    :class:`ListItemButton`s and one :class:`ListItemLabel`. Illustrates how
    to construct the fairly involved args_converter used with
    :class:`CompositeListItem`.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(MainView, self).__init__(**kwargs)

        # This is quite an involved args_converter, so we should go through the
        # details. A CompositeListItem instance is made with the args returned
        # by this converter. The first three, text, size_hint_y, height are
        # arguments for CompositeListItem. The cls_dicts list contains argument
        # sets for each of the member widgets for this composite:
        # ListItemButton and Label.
        def left_button_args(data_item):
            return {
                'component_class': ListItemButton,
                'component_kwargs': {'text': str(data_item.x1)}}

        def middle_label_args(data_item):
            return {
                'component_class': Label,
                'component_kwargs': {'text': "x10={0}".format(data_item.x10)}}

        def right_button_args(data_item):
            return {
                'component_class': ListItemButton,
                'component_kwargs': {'text': str(data_item.x100_text)}}

        args_converter = lambda index, data_item: \
            {'text': str(index),
             'size_hint_y': None,
             'height': 25,
             'bind_selection_from_children': True,
             'component_args': [left_button_args(data_item),
                                middle_label_args(data_item),
                                right_button_args(data_item)]}

        i_mult_data = \
            [IntegerDataItem(
                x1=i, x10=i * 10, x100_text= 'x100={0}'.format(i * 100))
                    for i in range(100)]

        controller = ListController(data=i_mult_data,
                                    selection_mode='single',
                                    allow_empty_selection=False)

        self.add_widget(ListView(data_binding=DataBinding(source=controller),
                                 args_converter=args_converter,
                                 list_item_class=CompositeListItem))


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))

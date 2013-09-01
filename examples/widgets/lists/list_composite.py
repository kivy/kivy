from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import CompositeListItem
from kivy.uix.listview import ListView
from kivy.uix.gridlayout import GridLayout


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
        def left_button_args(rec, key):
            return {'cls': ListItemButton, 'kwargs': {'text': key}}

        def middle_label_args(rec, key):
            return {
                'cls': Label,
                'kwargs': {'text': "x10={0}".format(rec['x10'])}}

        def right_button_args(rec, key):
            return {
                'cls': ListItemButton,
                'kwargs': {'text': str(rec['x100_text'])}}

        args_converter = lambda index, rec, key: \
            {'text': key,
             'size_hint_y': None,
             'height': 25,
             'carry_selection_to_children': True,
             'bind_selection_from_children': True,
             'cls_dicts': [left_button_args(rec, key),
                           middle_label_args(rec, key),
                           right_button_args(rec, key)]}

        integers_dict = \
            {str(i): {'x10': i * 10,
                       'x100_text': 'x100={0}'.format(i * 100),
                       'is_selected': False} for i in range(100)}

        item_strings = ["{0}".format(index) for index in range(100)]

        dict_adapter = DictAdapter(sorted_keys=item_strings,
                                   data=integers_dict,
                                   args_converter=args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)

        # Use the adapter in our ListView:
        list_view = ListView(adapter=dict_adapter)

        self.add_widget(list_view)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))

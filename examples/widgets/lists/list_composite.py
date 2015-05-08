from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.listview import ListItemButton, ListItemLabel, \
        CompositeListItem, ListView
from kivy.uix.gridlayout import GridLayout

from fixtures import integers_dict


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
        # details. A CompositeListItem instance is made with the args
        # returned by this converter. The first three, text, size_hint_y,
        # height are arguments for CompositeListItem. The cls_dicts list
        # contains argument sets for each of the member widgets for this
        # composite: ListItemButton and ListItemLabel.
        args_converter = lambda row_index, rec: {
            'text': rec['text'],
            'size_hint_y': None,
            'height': 25,
            'cls_dicts': [{'cls': ListItemButton,
                           'kwargs': {'text': rec['text']}},
                           {
                               'cls': ListItemLabel,
                               'kwargs': {
                                   'text': "Middle-{0}".format(rec['text']),
                                   'is_representing_cls': True}},
                           {
                               'cls': ListItemButton,
                               'kwargs': {'text': rec['text']}}]}

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

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
        kwargs['size_hint'] = (1.0, 1.0)
        super(MainView, self).__init__(**kwargs)

        # This is quite an involved args_converter, so we should go
        # through the details. x here is a data item object, be it
        # a string for a typical usage, as here, or some other object.
        # x will become the text value when the class used in this
        # example, CompositeListItem, is instantiated with the args
        # returned by this converter. All of the rest, for size_hint_y,
        # height, and the cls_dicts list, will be passed in the call
        # to instantiate CompositeListItem for a data item. Inside the
        # constructor of CompositeListItem is special-handling code that
        # uses cls_dicts to create, in turn, the component items in the
        # composite. This is a similar approach to using a kv template,
        # which you might wish to explore also.
        args_converter = \
            lambda rec: \
                {'text': rec['text'],
                 'size_hint_y': None,
                 'height': 25,
                 'cls_dicts': [{'cls': ListItemButton,
                                'kwargs': {'text': rec['text']}},
                               {'cls': ListItemLabel,
                                'kwargs': {'text': "Middle",
                                           'merge_text': True,
                                           'delimiter': '-',
                                           'is_representing_cls': True}},
                               {'cls': ListItemButton, 
                                'kwargs': {'text': rec['text']}}]}

        item_strings = ["{0}".format(index) for index in xrange(100)]

        # And now the list adapter, constructed with the item_strings as
        # the data, a dict to add the required is_selected boolean onto
        # data records, and our args_converter() that will operate one each
        # item in the data to produce list item view instances from the
        # :class:`CompositeListItem` class.
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

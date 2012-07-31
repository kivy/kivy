from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.mixins.selection import SelectableItem
from kivy.uix.listview import ListItemButton, ListItemLabel, \
        CompositeListItem, ListView

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, ListProperty


class MainView(GridLayout):
    '''Implementation of a list view with a composite list item class, with
    two buttons and a label.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['size_hint'] = (1.0, 1.0)
        super(MainView, self).__init__(**kwargs)

        args_converter = \
            lambda x: {'text': x,
                       'size_hint_y': None,
                       'height': 25,
                       'cls_dicts': [{'cls': ListItemButton,
                                      'kwargs': {'text': "Left",
                                                 'merge_text': True,
                                                 'delimiter': '-'}},
                                     {'cls': ListItemLabel,
                                      'kwargs': {'text': "Middle",
                                                 'merge_text': True,
                                                 'delimiter': '-',
                                                 'is_representing_cls': True}},
                                     {'cls': ListItemButton,
                                      'kwargs': {'text': "Right",
                                                 'merge_text': True,
                                                 'delimiter': '-'}}]}
                     
        # Here we create a list adapter with some item strings, passing our
        # CompositeListItem as the list item view class, and then we create a
        # list view using this adapter:
        item_strings = ["{0}".format(index) for index in xrange(100)]
        list_adapter = ListAdapter(data=item_strings,
                                   args_converter=args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)
        list_view = ListView(adapter=list_adapter)

        self.add_widget(list_view)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    runTouchApp(MainView(width=800))

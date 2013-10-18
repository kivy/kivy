from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton

from fixtures import fruit_data


class ReceivingFruitsDictAdapter(DictAdapter):

    def fruits_changed(self, *args):
        fruits_dict_adapter = args[0]

        if fruits_dict_adapter.selection:

            self.sorted_keys = \
                [sel.text for sel in fruits_dict_adapter.selection]


class TwoUpView(GridLayout):
    '''Implementation of a two-list widget, with a scrollable list of fruits
    on the left and a list on the right that shows items selected in the
    first list. It illustrates multiple selection in the left list and binding
    to a custom dict adapter.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        super(TwoUpView, self).__init__(**kwargs)

        list_item_args_converter = \
                lambda row_index, rec, key: {'text': key,
                                             'size_hint_y': None,
                                             'height': 25}

        fruits_dict_adapter = \
                DictAdapter(
                    sorted_keys=sorted(fruit_data.keys()),
                    data=fruit_data,
                    args_converter=list_item_args_converter,
                    selection_mode='multiple',
                    allow_empty_selection=False,
                    cls=ListItemButton)

        fruits_list_view = ListView(adapter=fruits_dict_adapter,
                                    size_hint=(.2, 1.0))

        self.add_widget(fruits_list_view)

        fruits_dict_adapter2 = \
                ReceivingFruitsDictAdapter(
                    sorted_keys=[item.text for item in fruits_dict_adapter.selection],
                    data=fruit_data,
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=True,
                    cls=ListItemButton)

        fruits_list_view2 = ListView(adapter=fruits_dict_adapter2,
                                     size_hint=(.2, 1.0))

        fruits_dict_adapter.bind(
                selection=fruits_dict_adapter2.fruits_changed)

        self.add_widget(fruits_list_view2)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(TwoUpView(width=800))

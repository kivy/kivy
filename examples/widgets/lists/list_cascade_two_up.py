from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton

from fixtures import fruit_data

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another, this time
# to have one list allow multiple selection and the other to show the
# multiple items selected in the first.


class ReceivingFruitsDictAdapter(DictAdapter):

    def fruits_changed(self, fruits_dict_adapter, *args):
        print 'fruits_changed called'
        if len(fruits_dict_adapter.selection) == 0:
            self.data = {}
            return

        data = {}
        for key in fruits_dict_adapter.selected_keys:
            data[key] = fruits_dict_adapter.data[key]
        self.data = data
        print 'data just set', data


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left, a list of fruits for the selected
    category in the middle, and a detail view on the right.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        kwargs['size_hint'] = (1.0, 1.0)
        super(CascadingView, self).__init__(**kwargs)

        list_item_args_converter = lambda rec: {'text': rec['name'],
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
                    sorted_keys=[],
                    data={},
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=True,
                    cls=ListItemButton)

        fruits_list_view2 = ListView(adapter=fruits_dict_adapter2,
                                     size_hint=(.2, 1.0))

        fruits_dict_adapter.bind(
                on_selection_change=fruits_dict_adapter2.fruits_changed)

        self.add_widget(fruits_list_view2)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    runTouchApp(CascadingView(width=800))

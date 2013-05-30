from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.dictadapter import DictAdapter

from fixtures import fruit_data

from fruit_detail_view import FruitDetailView


class MasterDetailView(GridLayout):
    '''Implementation of an master-detail view with a vertical scrollable list
    on the left (the master, or source list) and a detail view on the right.
    When selection changes in the master list, the content of the detail view
    is updated.
    '''

    def __init__(self, items, **kwargs):
        kwargs['cols'] = 2
        super(MasterDetailView, self).__init__(**kwargs)

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['name'],
                                        'size_hint_y': None,
                                        'height': 25}

        dict_adapter = DictAdapter(sorted_keys=sorted(fruit_data.keys()),
                                   data=fruit_data,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        master_list_view = ListView(adapter=dict_adapter,
                                    size_hint=(.3, 1.0))

        self.add_widget(master_list_view)

        detail_view = FruitDetailView(
                fruit_name=dict_adapter.selection[0].text,
                size_hint=(.7, 1.0))

        dict_adapter.bind(on_selection_change=detail_view.fruit_changed)
        self.add_widget(detail_view)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    master_detail = MasterDetailView(sorted(fruit_data.keys()), width=800)

    runTouchApp(master_detail)

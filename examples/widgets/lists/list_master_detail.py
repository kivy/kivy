from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.dictadapter import DictAdapter

from fixtures import fruit_data

from fruit_detail_view import FruitDetailView

# A "master-detail" view is a good way to experiment with a listview
# (the master) and another view (detail view) that gets updated upon
# selection.


class MasterDetailView(GridLayout):
    '''Implementation of an MasterDetailView with a vertical scrollable list
    on the left (the master, or source list) and a detail view on the right.
    '''

    def __init__(self, items, **kwargs):
        kwargs['cols'] = 2
        kwargs['size_hint'] = (1.0, 1.0)
        super(MasterDetailView, self).__init__(**kwargs)

        list_item_args_converter = lambda rec: {'text': rec['name'],
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

        detail_view = FruitDetailView(size_hint=(.7, 1.0))
        self.add_widget(detail_view)

        dict_adapter.bind(on_selection_change=detail_view.fruit_changed)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display.
        dict_adapter.touch_selection()


if __name__ == '__main__':

    from kivy.base import runTouchApp

    master_detail = MasterDetailView(sorted(fruit_data.keys()), width=800)

    runTouchApp(master_detail)

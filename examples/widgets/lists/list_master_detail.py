from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.listadapter import ListAdapter

from datastore_fruit_data import fruit_data, datastore_fruits

from detail_view import DetailView

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

        list_item_args_converter = lambda x: {'text': x,
                                              'size_hint_y': None,
                                              'height': 25}
        list_adapter = ListAdapter(data=sorted(fruit_data.keys()),
                                   datastore=datastore_fruits,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)
        master_list_view = ListView(adapter=list_adapter,
                                    size_hint=(.3, 1.0))
        self.add_widget(master_list_view)

        detail_view = DetailView(size_hint=(.7, 1.0))
        self.add_widget(detail_view)

        list_adapter.bind(on_selection_change=detail_view.on_selection_change)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display.
        list_adapter.touch_selection()


if __name__ == '__main__':

    from kivy.base import runTouchApp

    master_detail = MasterDetailView(sorted(fruit_data.keys()), width=800)

    runTouchApp(master_detail)

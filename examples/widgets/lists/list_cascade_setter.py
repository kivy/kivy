from kivy.adapters.listadapter import ListAdapter, AccumulatingListAdapter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton

from datastore_fruit_data import raw_fruit_data, datastore_fruits

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another, this time
# to have one list allow multiple selection and the other to show the
# multiple items selected in the first.

# This example uses a binding set from the selection of the first list to the
# data of the second, by use of the setter() method on the "to" side of the
# binding.

class MultipleCascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruits on the left and the selection in that list on the right in
    a second list.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        kwargs['size_hint'] = (1.0, 1.0)
        super(MultipleCascadingView, self).__init__(**kwargs)

        list_item_args_converter = lambda x: {'text': str(x),
                                              'size_hint_y': None,
                                              'height': 25}

        fruits = sorted([fruit_dict['name'] for fruit_dict in raw_fruit_data])
        fruits_list_adapter = \
                ListAdapter(data=fruits,
                            datastore=datastore_fruits,
                            args_converter=list_item_args_converter,
                            selection_mode='multiple',
                            allow_empty_selection=False,
                            cls=ListItemButton)
        fruits_list_view = \
                ListView(adapter=fruits_list_adapter,
                        size_hint=(.2, 1.0))
        self.add_widget(fruits_list_view)

        # Selected fruits, on the right
        #
        selected_fruits_list_adapter = \
                ListAdapter(
                    data=[fruits[0]],
                    datastore=datastore_fruits,
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=True,
                    cls=ListItemButton)
        selected_fruits_list_view = \
                ListView(adapter=selected_fruits_list_adapter,
                    size_hint=(.2, 1.0))
        fruits_list_adapter.bind(
                selection=selected_fruits_list_adapter.setter('data'))
        self.add_widget(selected_fruits_list_view)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    # All fruit categories will be shown in the left left (first argument),
    # and the first category will be auto-selected -- Melons. So, set the
    # second list to show the melon fruits (second argument).
    runTouchApp(MultipleCascadingView(width=800))

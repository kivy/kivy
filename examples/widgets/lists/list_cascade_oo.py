from kivy.adapters.objectadapter import ObjectAdapter
from kivy.adapters.listadapter import ListAdapter, ListsAdapter
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.observerview import ObserverView
from kivy.properties import ObjectProperty

from fruit_data import fruit_categories

from fruit_detail_view import FruitObserverDetailView

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another. In this
# example the lists are restricted to single selection. The list on the
# left is a simple list. The list in the middle is specialized for
# observing the selection in the first, and using that item as the key
# into a dict providing its own list items. The view on the right is
# the sames as the DetailView in the master-detail example.


# What is oo, you say? 
#
#     ...  An example featuring ObserverView and ObjectAdapter
#

class FruitsListAdapter(ListAdapter):

    def fruit_category_changed(self, fruit_categories_adapter, *args):
        if len(fruit_categories_adapter.selection) == 0:
            # Do we need to store previous selection? Need to unselect items?
            self.data = []
            return

        self.data = \
                fruit_categories[str(fruit_categories_adapter.selection[0])]


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left (source list), a list of fruits for the
    selected category in the middle, and a detail view on the right.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        kwargs['size_hint'] = (1.0, 1.0)
        super(CascadingView, self).__init__(**kwargs)

        list_item_args_converter = lambda x: {'text': x,
                                              'size_hint_y': None,
                                              'height': 25}

        # Fruit categories list on the left:
        #
        categories = sorted(fruit_categories.keys())
        fruit_categories_list_adapter = \
            ListAdapter(data=categories,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)
        fruit_categories_list_view = \
                ListView(adapter=fruit_categories_list_adapter,
                        size_hint=(.2, 1.0))
        self.add_widget(fruit_categories_list_view)

        # Fruits, for a given category, in the middle:
        #

        # List adapter option #1
        #
        #     - use ListsAdapter, which takes observed_list_adapter as an
        #       argument and sets up the binding for you. You also have to
        #       pass lists_dict.
        #
        #fruits_list_adapter = \
                #ListsAdapter(
                    #observed_list_adapter=fruit_categories_list_adapter,
                    #lists_dict=fruit_categories,
                    #data=fruit_categories[categories[0]],
                    #args_converter=list_item_args_converter,
                    #selection_mode='single',
                    #allow_empty_selection=False,
                    #cls=ListItemButton)

        # List adapter option #2
        #
        #     - use the custom FruitsListsAdapter, defined above. It has a
        #       fruit_changed() method, performing the same role as the
        #       on_selection_change() function of ListsAdapter in Option #1.
        #       In option #2, you are responsible for setting up the binding
        #       after the instantiation of the list adapter.
        #
        fruits_list_adapter = \
                FruitsListAdapter(
                    data=fruit_categories[categories[0]],
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)
        fruit_categories_list_adapter.bind(
            on_selection_change=fruits_list_adapter.fruit_category_changed)

        fruits_list_view = \
                ListView(adapter=fruits_list_adapter,
                    size_hint=(.2, 1.0))

        self.add_widget(fruits_list_view)

        # For the fruit detail view on the right, this is ObserverView, which
        # uses ObjectAdapter.
        #
        fruit_detail_view = ObserverView(adapter=ObjectAdapter(
                obj_bind_from=fruits_list_adapter,
                args_converter=lambda x: {'fruit_name': str(x),
                                          'size_hint': (.6, 1.0)},
                cls=FruitObserverDetailView))

        self.add_widget(fruit_detail_view)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display. [TODO] Surely there is a way to avoid this.
        fruits_list_adapter.touch_selection()


if __name__ == '__main__':

    from kivy.base import runTouchApp

    # All fruit categories will be shown in the left left (first argument),
    # and the first category will be auto-selected -- Melons. So, set the
    # second list to show the melon fruits (second argument).
    runTouchApp(CascadingView(width=800))

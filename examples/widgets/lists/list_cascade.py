from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.models import SelectableDataItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton

from fixtures import fruit_categories, fruit_data_list_of_dicts

from fruit_detail_view import FruitDetailView

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another. In this
# example the lists are restricted to single selection. The list on the
# left is a simple list. The list in the middle is specialized for
# observing the selection in the first, and using that item as the key
# into a dict providing its own list items. The view on the right is
# the same as the DetailView in the master-detail example.

# A custom adapter is needed here, because we must transform the selected
# fruit category into the list of fruits for that category.


class FruitsListAdapter(ListAdapter):

    def fruit_category_changed(self, fruit_categories_adapter, *args):
        if len(fruit_categories_adapter.selection) == 0:
            self.data = []
            return

        category = \
                fruit_categories[fruit_categories_adapter.selection[0].text]

        # We are responsible with resetting the data. In this example, we are
        # using lists of instances of the classes defined below, CategoryItem
        # and FruitItem. We assume that the names of the fruits are unique,
        # so we look up items by name.
        #
        self.data = \
            [f for f in fruit_data_items if f.name in category['fruits']]

        # Also, see the examples that use dict records.


# FruitsListAdapter subclasses ListAdapter, which has SelectionSupport mixed
# in. SelectionSupport requires that data items handle selection operations.
# This means that we can't have simple strings as data items, nor can we have
# items that don't comply with SelectionSupport needs. It is not difficult to
# make your own data items, however, because you can define custom data item
# classes that subclass SelectableDataItem:
#
class CategoryItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(CategoryItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.fruits = kwargs.get('fruits', [])
        self.is_selected = kwargs.get('is_selected', False)


class FruitItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')
        self.data = kwargs.get('data', [])
        self.is_selected = kwargs.get('is_selected', False)


# To instantiate CategoryItem and FruitItem instances, we use the dictionary-
# style fixtures data in fruit_data (See import above), which is
# also used by other list examples. The double asterisk usage here is for
# setting arguments from a dict in calls to instantiate the custom data item
# classes defined above.

# fruit_categories is a dict of dicts.
category_data_items = \
    [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]

# fruit_data_list_of_dicts is a list of dicts, already sorted.
fruit_data_items = \
    [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]

# We end up with two normal lists of objects, to be used for two list views
# defined below.


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left, a list of fruits for the selected
    category in the middle, and a detail view on the right.

    This example uses :class:`ListAdapter`. See an equivalent treatment that
    uses :class:`DictAdapter` in list_cascade_dict.py.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        super(CascadingView, self).__init__(**kwargs)

        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        # Add a fruit categories list on the left. We use ListAdapter, for
        # which we set the data argument to the list of CategoryItem
        # instances from above. The args_converter only pulls the name
        # property from these instances, adding also size_hint_y and height.
        # selection_mode is single, because this list will "drive" the second
        # list defined below. allow_empty_selection is False, because we
        # always want a selected category, so that the second list will be
        # populated. Finally, we instruct ListAdapter to build list item views
        # using the provided cls, ListItemButton.
        #
        fruit_categories_list_adapter = \
            ListAdapter(data=category_data_items,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        fruit_categories_list_view = \
                ListView(adapter=fruit_categories_list_adapter,
                         size_hint=(.2, 1.0))

        self.add_widget(fruit_categories_list_view)

        # Fruits, for a given category, are in a list in the middle, which
        # uses FruitsListsAdapter, defined above. FruitsListAdapter has a
        # fruit_changed() method that updates the data list. The binding
        # to the fruit_categories_list_adapter is set up after
        # instantiation of the fruit_list_adapter.
        #
        first_category_fruits = \
            fruit_categories[fruit_categories.keys()[0]]['fruits']

        first_category_fruit_data_items = \
            [f for f in fruit_data_items if f.name in first_category_fruits]

        fruits_list_adapter = \
                FruitsListAdapter(data=first_category_fruit_data_items,
                                  args_converter=list_item_args_converter,
                                  selection_mode='single',
                                  allow_empty_selection=False,
                                  cls=ListItemButton)

        fruit_categories_list_adapter.bind(
            on_selection_change=fruits_list_adapter.fruit_category_changed)

        fruits_list_view = \
                ListView(adapter=fruits_list_adapter, size_hint=(.2, 1.0))

        self.add_widget(fruits_list_view)

        # Detail view, for a given fruit, on the right:
        #
        detail_view = FruitDetailView(
                fruit_name=fruits_list_adapter.selection[0].text,
                size_hint=(.6, 1.0))

        fruits_list_adapter.bind(
                on_selection_change=detail_view.fruit_changed)
        self.add_widget(detail_view)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    runTouchApp(CascadingView(width=800))

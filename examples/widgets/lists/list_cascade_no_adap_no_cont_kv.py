from kivy.app import App
from kivy.binding import Binding
from kivy.controllers.objectcontroller import ObjectController
from kivy.controllers.transformcontroller import TransformController
from kivy.enums import binding_modes
from kivy.enums import binding_transforms
from kivy.lang import Builder
from kivy.models import SelectableDataItem
from kivy.properties import StringProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListView
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import SelectableView
from kivy.uix.objectview import ObjectView

from fixtures import fruit_categories
from fixtures import fruit_data
from fixtures import fruit_data_list_of_dicts
from fixtures import fruit_data_attributes

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another. In this
# example the lists are restricted to single selection. The list on the
# left is a simple list. The list in the middle is specialized for
# observing the selection in the first, and using that item as the key
# into a dict providing its own list items. The view on the right is
# the same as the DetailView in the master-detail example.

# It is not difficult to make your own data items, because you can define
# custom data item classes that subclass SelectableDataItem:


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


# Utility functions, in this case we have one, a transform function for use in
# binding together our two list views below. In a real app (bigger), perhaps
# these would be stored in a utility module for clear code organization. Here
# we have access to the two data lists as globals, but if used in a utils.py
# module, for example, perhaps there would be path references such as
# app.fruit_data_items.
def fruit_data_items_for_category_view(view):
    return [f for f in fruit_data_items
            if f.name in category_data_items[view.index].fruits]

list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}


class FruitDetailViewInPython(GridLayout, SelectableView):

    text = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['size_hint'] = (1, None)

        super(FruitDetailView, self).__init__(**kwargs)

        self.bind(minimum_height=self.setter('height'))

        self.add_widget(Label(text="Name:",
                              size_hint_y=None,
                              height=50,
                              halign='right'))

        self.add_widget(Label(text=self.text,
                              size_hint_y=None,
                              height=50))

        for attribute in fruit_data_attributes:
            self.add_widget(Label(text="{0}:".format(attribute),
                                  size_hint_y=None,
                                  height=50,
                                  halign='right'))
            self.add_widget(
                Label(text=str(fruit_data[self.text][attribute]),
                      size_hint_y=None,
                      height=50))


Builder.load_string("""
#:import Binding kivy.binding.Binding
#:import binding_modes kivy.enums.binding_modes
#:import binding_transforms kivy.enums.binding_transforms

<FruitDetailView@GridLayout, SelectableView>:
    cols: 2
    size_hint: 1, None
    text: None

    Label:
        text: 'Name:'
        size_hint_y: None
        height: 50
        halign: 'right'

    Label:
        text: root.text
        size_hint_y: None
        height: 50

<CascadingView>:
    cols: 3
    fruit_categories_list_view: fruit_categories_list_view
    fruits_list_view: fruits_list_view
    fruit_view: fruit_view

    ListView:
        id: fruit_categories_list_view
        data: category_data_items
        args_converter: list_item_args_converter
        selection_mode: 'single'
        allow_empty_selection: False
        cls: ListItemButton
        size_hint: .2, 1.0

    ListView:
        id: fruits_list_view
        data: Binding(source=root.fruit_categories_list_view.adapter, \
                      prop='selection', \
                      mode=binding_modes.FIRST_ITEM, \
                      transform=fruit_data_items_for_category_view)
        args_converter: list_item_args_converter
        selection_mode: 'single'
        allow_empty_selection: False
        cls: ListItemButton
        size_hint: .2, 1.0

    ObjectView:
        id: fruit_view
        data: Binding(source=root.fruits_list_view.adapter, \
                      prop='selection', \
                      mode=binding_modes.FIRST_ITEM, \
                      transform=(binding_transforms.TRANSFORM, \
                                 lambda v: root.fruits_list_view.adapter.data[v.index]))
        args_converter: lambda row_index, fruit: {'text': fruit.name}
        selection_mode: 'single'
        allow_empty_selection: False
        cls: FruitDetailView
        size_hint: .6, 1.0
""")


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left, a list of fruits for the selected
    category in the middle, and a detail view on the right.

    This example uses :class:`ListAdapter`. See an equivalent treatment that
    uses :class:`DictAdapter` in list_cascade_dict.py.
    '''
    pass


if __name__ == '__main__':

    from kivy.base import runTouchApp

    runTouchApp(CascadingView(width=800))


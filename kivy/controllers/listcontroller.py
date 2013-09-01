'''
ListController
--------------

The ListController class redefines data as a ListProperty that uses the
OpObservableList class internally, in the same way the ListProperty used in
ListAdapter does.

The default update() method for setting data will set a list to data, and will
put another type inside a new list before setting to data.

List controllers are general purpose data containers that have the benefit of
Kivy properties and bindings. Especially useful are AliasProperty instances
that act as computed properties, calculated from one or more additional
properties. Methods in list controllers can do filtering of the data for
convenience and efficiency. Using such methods, an API for the list data can be
constructed.

As a convenience for setting up alias properties, use FilterProperty or
MapProperty to hold code to filter or transform data:

    FruitsController(ListController):

        small_fruits = FilterProperty(lambda item: item.size() < 40)
        medium_fruits = FilterProperty(lambda item: 40 <= item.size() < 80)
        big_fruits = FilterProperty(lambda item: item.size() >= 80)

With no arguments to a FilterProperty or MapProperty, the function, in these
examples a lambda, is applied on controller.data, for which bindings are
automatically set. (This is where the convenience, over making your own
AliasProperty, comes in).

You can also use filter and map properties as dependencies of other properties
by setting data.

    TreesController(ListController):

        conifers = ListProperty(['Loblolly Pine',
                                 'Norfolk Island Pine',
                                 'Monterey Cypress'])

        angiosperms = ListProperty(['White Oak',
                                    'Live Oak',
                                    'Buttercup Oak',
                                    'Water Oak',
                                    'Pin Oak',
                                    'Geranium',
                                    'Petunia'])

        pines = FilterProperty(lambda item: 'Pine' in item, data='conifers')
        oaks = FilterProperty(lambda item: 'Oak' in item, data='angiosperms')

You can chain computed properties, as in:

    FruitsController(ListController):

        ...
        tiny_fruits = FilterProperty(lambda item: item.size() < 10,
                                     data='small_fruits')

Additional dependencies for the function (as for the getter in an
AliasProperty) can be specified in the bind argument:

    VotesController(ListController):

        # data, by default, is the main subject of the maps and filters

        f1 = NumericProperty()
        f2 = NumericProperty()
        rankings = MapProperty(lambda item: __some ranking function__,
                               bind=['f1', 'f2'])

        trending = \
            MapProperty(lambda item: self.rankings[item.index] / self.f1,
                               bind=['rankings', 'f1'])

For more specialized needs, add your own AliasProperty to the controller or
adapter, along with needed getter and setting methods.

List controllers can be used in combination, with bindings between their data
and/or selection properties. Another common use is to have an ObjectController
hold the single selection from a ListController.

.. versionadded:: 1.8

'''

from kivy.properties import OpObservableList
from kivy.properties import ListProperty
from kivy.selection import Selection

from kivy.controllers.controller import Controller
from kivy.controllers.list_ops import ControllerListOpHandler
from kivy.controllers.utils import parse_binding
from kivy.controllers.utils import bind_binding

__all__ = ('ListController', )


class ListController(Selection, Controller):

    data = ListProperty([], cls=OpObservableList)

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):

        data_binding, kwargs = parse_binding('data', kwargs)
        selection_binding, kwargs = parse_binding('selection', kwargs)

        super(ListController, self).__init__(**kwargs)

        if data_binding:
            bind_binding(self, data_binding)
        if selection_binding:
            bind_binding(self, selection_binding)

        self.list_op_handler = \
                ControllerListOpHandler(source_list=self.data,
                                        duplicates_allowed=True)

        self.bind(data=self.list_op_handler.data_changed)

    def update_data_from_first_item(self, *args):
        # For data, we set as a list with the only item as the first item.
        l = args[1]
        if l:
            self.data = [l[0]]

    def update_selection_from_first_item(self, *args):
        # For selection, we set as a list with the only item as the first item.
        l = args[1]
        if l:
            self.selection = [l[0]]

    # TODO: See comment in ListAdapter about getting rid of this event, and
    # just relying on observing data.
    def on_data_change(self, *args):
        '''on_data_change() is the default handler for the on_data_change
        event.
        '''
        pass

    def get_count(self):
        return len(self.data)

    def get_selectable_item(self, index):

        if index < 0 or index > len(self.data) - 1:
            return None

        return self.data[index]

    def update(self, *args):
        # args:
        #
        #     controller args[0]
        #     value      args[1]
        #     op_info    args[2]

        value = args[1]

        if isinstance(value, list):
            self.data = value
        else:
            if value:
                self.data = [value]

    #################################
    # FILTERS and ALIAS PROPERTIES

    def all(self):
        return self.data

    def reversed(self):
        return reversed(self.data)

    def first(self):
        return self.data[0]

    def last(self):
        return self.data[-1]

    def add(self, item):
        self.data.append(item)

    def delete(self, item):
            self.data.remove(item)

    def sorted(self):
        return sorted(self.data)

    # TODO: There can also be an order_by or other aid for sorting.

    # TODO: Add examples of filtering and alias properties in
    #       examples/controllers/.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item if there is a selection.
        '''
        if len(self.selection) > 0:
            first_sel_index = \
                    min([self.data.index(sel) for sel in self.selection])
            self.data = self.data[first_sel_index:]

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item if there is a selection.
        '''
        if len(self.selection) > 0:
            last_sel_index = \
                    max([self.data.index(sel) for sel in self.selection])
            self.data = self.data[:last_sel_index + 1]

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item if there is a
        selection. This preserves intervening list items within the selected
        range.
        '''
        if len(self.selection) > 0:
            sel_indices = [self.data.index(sel) for sel in self.selection]
            first_sel_index = min(sel_indices)
            last_sel_index = max(sel_indices)
            self.data = self.data[first_sel_index:last_sel_index + 1]

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.
        '''
        if len(self.selection) > 0:
            self.data = self.selection

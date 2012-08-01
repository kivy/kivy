from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.mixins.selection import SelectableItem
from kivy.adapters.listadapter import ListAdapter

from fruit_data import fruit_data

from detail_view import DetailView

# [TODO] NOTE -- This is a copy of the old version of list_master_detail.py,
#                because it contains an example of how to make a custom
#                ListItem.
#
#                Calling this example "disclosure" because plan is to try
#                expanding a row to show a detail view when the disclosure
#                button for a row is clicked.
#
#                Something like this:
#
#                     http://www.zkoss.org/zkdemo/grid/master_detail
#
# Master-Detail view for showing a list on the left (the master) and a view
# on the right for the detail view.

# A "master-detail" view is a good way to experiment with a listview
# (the master) and another view (detail view) that gets updated upon selection.


# MASTER list

# For the master list, we need to create a custom "list item" type that
# subclasses SelectableItem.

# A composite list item could consist of a button on the left, several labels
# in the middle, and another button on the right. Not sure of the merit of
# allowing, perhaps, some "sub" list items to react to touches and others not,
# if that were to be enabled.


class CompositeListItem(SelectableItem, BoxLayout):
    # CompositeListItem (BoxLayout) by default uses orientation='horizontal',
    # but could be used also for a side-to-side display of items.
    #
    # ListItemButton sublasses Button, which has background_color.
    # Here we must add this property.
    background_color = ListProperty([1, 1, 1, 1])

    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = ListProperty([.33, .33, .33, 1])

    icon_button = ObjectProperty(None)
    content_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CompositeListItem, self).__init__(**kwargs)

        # Now this button just has text '>', but it would be neat to make the
        # left button hold icons -- the list would be heterogeneous, containing
        # different list item types that could be filtered perhaps (an option
        # for selecting all of a given type, for example).

        # For sub list items, set selection_target to self (this is a kind of
        # composite list item) so that when they are touched, the composite
        # list item is selected, not the components. Any list item component
        # that should be selected individually, would need to override this.
        kwargs['selection_target'] = self

        # Make a copy of kwargs and add specific args for the "disclosure"
        # icon button.
        icon_kwargs = kwargs.copy()
        icon_kwargs['text'] = '>'
        icon_kwargs['size_hint_x'] = .05
        self.icon_button = ListItemButton(**icon_kwargs)

        # Use the passed in kwargs for the "content" button.
        self.content_button = ListItemButton(**kwargs)

        self.add_widget(self.icon_button)
        self.add_widget(self.content_button)

    def select(self, *args):
        self.background_color = self.selected_color

    def deselect(self, *args):
        self.background_color = self.deselected_color

    def __repr__(self):
        if self.content_button is not None:
            return self.content_button.text
        else:
            return 'empty'


class MasterDetailView(GridLayout):
    '''Implementation of an MasterDetailView with a vertical scrollable list
    on the left (the master, or source list) and a detail view on the right.
    '''

    def __init__(self, items, **kwargs):
        kwargs['cols'] = 2
        kwargs['size_hint'] = (1.0, 1.0)
        super(MasterDetailView, self).__init__(**kwargs)

        args_converter = lambda x: {'text': x,
                                    'size_hint_y': None,
                                    'height': 25}
        list_adapter = ListAdapter(data=items,
                                   args_converter=args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)
        master_list_view = ListView(adapter=list_adapter, size_hint=(.3, 1.0))
        self.add_widget(master_list_view)

        detail_view = DetailView(size_hint=(.7, 1.0))
        self.add_widget(detail_view)

        list_adapter.bind(on_selection_change=detail_view.on_selection_change)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display.
        list_adapter.touch_selection()


if __name__ == '__main__':

    from kivy.base import runTouchApp

    master_detail = MasterDetailView(fruit_data.keys(), width=800)

    runTouchApp(master_detail)

from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.mixins.selection import SelectableItem
from kivy.uix.listview import ListItemButton, ListItemLabel, ListView

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, ListProperty


class CompositeListItem(SelectableItem, BoxLayout):
    # ListItem sublasses Button, which has background_color.
    # For a composite list item, we must add this property.
    background_color = ListProperty([1, 1, 1, 1])

    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = ListProperty([.33, .33, .33, 1])

    left_button = ObjectProperty(None)
    middle_label = ObjectProperty(None)
    right_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CompositeListItem, self).__init__(**kwargs)

        # For the component list items in our composite list item, we want
        # their individual selection to select the composite. Here we pass
        # an argument for the list_adapter, required by the SelectableItem
        # mixing, and a selection_target argument, setting it to self (to
        # this composite list item).
        kwargs['selection_target'] = self

        kwargs['text']="left-{0}".format(kwargs['text'])
        self.left_button = ListItemButton(**kwargs)

        kwargs['text']="middle-{0}".format(kwargs['text'])
        self.middle_label = ListItemLabel(**kwargs)

        kwargs['text']="right-{0}".format(kwargs['text'])
        self.right_button = ListItemButton(**kwargs)

        self.add_widget(self.left_button)
        self.add_widget(self.middle_label)
        self.add_widget(self.right_button)

    def select(self, *args):
        self.background_color = self.selected_color

    def deselect(self, *args):
        self.background_color = self.deselected_color

    def __repr__(self):
        if self.middle_label is not None:
            return self.middle_label.text
        else:
            return 'empty'


class CompositeListItemListView(GridLayout):
    '''Implementation of a list view with a composite list item class, with
    two buttons and a label.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['size_hint'] = (1.0, 1.0)
        super(CompositeListItemListView, self).__init__(**kwargs)

        # Here we create a list adapter with some item strings, passing our
        # CompositeListItem as the list item view class, and then we create a
        # list view using this adapter:
        item_strings = ["{0}".format(index) for index in xrange(100)]
        list_adapter = ListAdapter(data=item_strings,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)
        list_view = ListView(adapter=list_adapter)

        self.add_widget(list_view)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    runTouchApp(CompositeListItemListView(width=800))

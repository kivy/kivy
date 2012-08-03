from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.mixins.selection import SelectableItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.lang import Builder
from kivy.factory import Factory

from fruit_data import fruit_categories

from fruit_detail_view import FruitImageDetailView

# This is a copy of list_cascade.py with image thumbnails added to the list
# item views and a larger image shown in the detail view for the selected
# fruit. It uses the kv template method for providing the list item view to
# the listview showing the list of fruits for a selected category.

Factory.register('SelectableItem', cls=SelectableItem)
Factory.register('ListItemButton', cls=ListItemButton)

Builder.load_string('''
[ThumbnailedListItem@SelectableItem+BoxLayout]:
    fruit_name: ctx.text
    size_hint_y: ctx.size_hint_y
    height: ctx.height
    Image
        source: "fruit_images/{0}.32.jpg".format(ctx.text)
    ListItemButton:
        text: ctx.text
''')


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
        image_list_item_args_converter = lambda x: {'text': x,
                                                    'size_hint_y': None,
                                                    'height': 32}
        fruits_list_adapter = \
                FruitsListAdapter(
                    data=fruit_categories[categories[0]],
                    args_converter=image_list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    template='ThumbnailedListItem')
        fruits_list_view = \
                ListView(adapter=fruits_list_adapter,
                    size_hint=(.2, 1.0))
        fruit_categories_list_adapter.bind(
            on_selection_change=fruits_list_adapter.fruit_category_changed)
        self.add_widget(fruits_list_view)

        # Detail view, for a given fruit, on the right:
        #
        detail_view = FruitImageDetailView(size_hint=(.6, 1.0))
        fruits_list_adapter.bind(
                on_selection_change=detail_view.fruit_changed)
        self.add_widget(detail_view)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display. [TODO] Surely there is a way to avoid this.
        fruits_list_adapter.touch_selection()


if __name__ == '__main__':

    from kivy.base import runTouchApp

    # All fruit categories will be shown in the left left (first argument),
    # and the first category will be auto-selected -- Melons. So, set the
    # second list to show the melon fruits (second argument).
    runTouchApp(CascadingView(width=800))

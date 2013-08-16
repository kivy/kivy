from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.listview import SelectableView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.lang import Builder
from kivy.factory import Factory

from fixtures import fruit_categories, fruit_data

from fruit_detail_view import FruitImageDetailView

# This is a copy of list_cascade.py with image thumbnails added to the list
# item views and a larger image shown in the detail view for the selected
# fruit. It uses the kv template method for providing the list item view to
# the listview showing the list of fruits for a selected category.

Factory.register('SelectableView', cls=SelectableView)
Factory.register('ListItemButton', cls=ListItemButton)

Builder.load_string('''
#:import SelectionTool kivy.selection.SelectionTool

[ThumbnailedListItem@SelectableView+BoxLayout]:
    index: ctx.index
    fruit_name: ctx.text
    size_hint_y: ctx.size_hint_y
    height: ctx.height
    carry_selection_to_children: True
    Image
        source: "fruit_images/{0}.32.jpg".format(ctx.text)
    ListItemButton:
        index: ctx.index
        text: ctx.text
        on_release: self.parent.trigger_action(duration=0)
''')


# A custom adapter is needed here, because we must transform the selected
# fruit category into the list of fruit keys for that category.
#
class FruitsDictAdapter(DictAdapter):

    def fruit_category_changed(self, *args):

        fruit_categories_adapter = args[0]

        if fruit_categories_adapter.selection:
            key = fruit_categories_adapter.selection[0].text

            category = fruit_categories[key]

            self.sorted_keys = category['fruits']


class CascadingView(GridLayout):
    '''Implementation of a cascading style display, with a scrollable list
    of fruit categories on the left, a list of thumbnailed fruit items for the
    selected category in the middle, and a detail view on the right that shows
    a larger fruit image with data.

    See list_cascade_dict.py for the same example without images.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        super(CascadingView, self).__init__(**kwargs)

        list_item_args_converter = \
                lambda row_index, rec, key: {'text': key,
                                             'size_hint_y': None,
                                             'height': 25}

        # Fruit categories list on the left:
        #
        categories = sorted(fruit_categories.keys())
        fruit_categories_list_adapter = \
            DictAdapter(
                    sorted_keys=categories,
                    data=fruit_categories,
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
        image_list_item_args_converter = \
                lambda row_index, rec, key: {'text': key,
                                             'size_hint_y': None,
                                             'height': 32}
        fruits_list_adapter = \
                FruitsDictAdapter(
                    sorted_keys=fruit_categories[categories[0]]['fruits'],
                    data=fruit_data,
                    args_converter=image_list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    template='ThumbnailedListItem')
        fruits_list_view = \
                ListView(adapter=fruits_list_adapter,
                    size_hint=(.2, 1.0))

        fruit_categories_list_adapter.bind(
                selection=fruits_list_adapter.fruit_category_changed)

        self.add_widget(fruits_list_view)

        # Detail view, for a given fruit, on the right:
        #
        detail_view = FruitImageDetailView(
                fruit_name=fruits_list_adapter.selection[0].fruit_name,
                size_hint=(.6, 1.0))

        fruits_list_adapter.bind(
                selection=detail_view.fruit_changed)
        self.add_widget(detail_view)


if __name__ == '__main__':

    from kivy.base import runTouchApp

    # All fruit categories will be shown in the left left (first argument),
    # and the first category will be auto-selected -- Melons. So, set the
    # second list to show the melon fruits (second argument).
    runTouchApp(CascadingView(width=800))

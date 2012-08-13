from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton

from fixtures import fruit_categories, fruit_categories, \
        fruit_data

from fruit_detail_view import FruitDetailView

# A custom adapter is needed here, because we must transform the selected
# fruit category into the list of fruit keys for that category.


class FruitsDictAdapter(DictAdapter):

    def fruit_category_changed(self, fruit_categories_adapter, *args):
        if len(fruit_categories_adapter.selection) == 0:
            self.data = {}
            return

        category = \
                fruit_categories[str(fruit_categories_adapter.selection[0])]
        self.sorted_keys = category['fruits']


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left, a list of fruits for the selected
    category in the middle, and a detail view on the right.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        kwargs['size_hint'] = (1.0, 1.0)
        super(CascadingView, self).__init__(**kwargs)

        list_item_args_converter = lambda rec: {'text': rec['name'],
                                                'size_hint_y': None,
                                                'height': 25}

        # Fruit categories list on the left:
        #
        categories = sorted(fruit_categories.keys())
        fruit_categories_dict_adapter = \
            DictAdapter(
                    sorted_keys=categories,
                    data=fruit_categories,
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)
        fruit_categories_list_view = \
                ListView(adapter=fruit_categories_dict_adapter,
                        size_hint=(.2, 1.0))
        self.add_widget(fruit_categories_list_view)

        fruits_dict_adapter = \
                FruitsDictAdapter(
                    sorted_keys=fruit_categories[categories[0]]['fruits'],
                    data=fruit_data,
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)

        fruit_categories_dict_adapter.bind(
            on_selection_change=fruits_dict_adapter.fruit_category_changed)

        fruits_list_view = \
                ListView(adapter=fruits_dict_adapter,
                    size_hint=(.2, 1.0))

        self.add_widget(fruits_list_view)

        # Detail view, for a given fruit, on the right:
        #
        detail_view = FruitDetailView(size_hint=(.6, 1.0))

        fruits_dict_adapter.bind(
                on_selection_change=detail_view.fruit_changed)
        self.add_widget(detail_view)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display.
        fruits_dict_adapter.touch_selection()


if __name__ == '__main__':

    from kivy.base import runTouchApp

    runTouchApp(CascadingView(width=800))

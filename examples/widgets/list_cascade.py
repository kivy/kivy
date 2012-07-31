from kivy.adapters.listadapter import ListAdapter, \
        SelectableListsAdapter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListView, ListItemButton
from kivy.properties import StringProperty

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another. In this
# example the lists are restricted to single selection. The list on the
# left is a simple list. The list in the middle is specialized for
# observing the selection in the first, and using that item as the key
# into a dict providing its own list items. The view on the right is
# the sames as the DetailView in the master-detail example.


class DetailView(GridLayout):
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(DetailView, self).__init__(**kwargs)
        self.bind(fruit_name=self.redraw)

    def redraw(self, *args):
        self.clear_widgets()
        self.add_widget(Label(text="Name:", halign='right'))
        self.add_widget(Label(text=self.fruit_name))
        for category in descriptors:
            self.add_widget(Label(text="{0}:".format(category),
                                  halign='right'))
            self.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][category])))

    def on_selection_change(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            return

        selected_object = list_adapter.selection[0]

        if type(selected_object) is str:
            self.fruit_name = selected_object
        else:
            self.fruit_name = str(selected_object)

        self.redraw()


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
        fruits_list_adapter = \
                SelectableListsAdapter(
                    observed_list_adapter=fruit_categories_list_adapter,
                    selectable_lists_dict=fruit_categories,
                    data=fruit_categories[categories[0]],
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)
        fruits_list_view = \
                ListView(adapter=fruits_list_adapter,
                    size_hint=(.2, 1.0))
        fruit_categories_list_adapter.bind(
                on_selection_change=fruits_list_adapter.on_selection_change)
        self.add_widget(fruits_list_view)

        # Detail view, for a given fruit, on the right:
        #
        detail_view = DetailView(
                observed_list_adapter=fruits_list_adapter,
                size_hint=(.6, 1.0))
        fruits_list_adapter.bind(
                on_selection_change=detail_view.on_selection_change)
        self.add_widget(detail_view)


# Data from http://www.fda.gov/Food/LabelingNutrition/\
#                FoodLabelingGuidanceRegulatoryInformation/\
#                InformationforRestaurantsRetailEstablishments/\
#                ucm063482.htm
fruit_categories = \
        {'Melons': ['Cantaloupe', 'Honeydew Melon', 'Watermelon'],
         'Tree Fruits': ['Apple', 'Avocado, California', 'Banana', 'Nectarine',
                         'Peach', 'Pear', 'Pineapple', 'Plums',
                         'Sweet Cherries'],
         'Citrus Fruits': ['Grapefruit', 'Lemon', 'Lime', 'Orange',
                           'Tangerine'],
         'Miscellaneous Fruits': ['Grapes', 'Kiwifruit', 'Strawberries']}
descriptors = """(gram weight/ ounce weight)	Calories	Calories from Fa
t	Total Fat	Sodium	Potassium	Total Carbo-hydrate	Dietary Fiber	Suga
rs	Protein	Vitamin A	Vitamin C	Calcium	Iron""".replace('\n', '')
descriptors = [item.strip() for item in descriptors.split('\t')]
units = """(g) 	(%DV)	(mg) 	(%DV)	(mg) 	(%DV)	 (g) 	(%DV)	 (g)
(%DV)	 (g) 	 (g) 	(%DV)	(%DV)	(%DV)	(%DV)""".replace('\n', '')
units = [item.strip() for item in units.split('\t')]
raw_fruit_data = [
{'name':'Apple',
 'Serving Size': '1 large (242 g/8 oz)',
 'data': [130, 0, 0, 0, 0, 0, 260, 7, 34, 11, 5, 20, 25, 1, 2, 8, 2, 2]},
{'name':'Avocado, California',
 'Serving Size': '1/5 medium (30 g/1.1 oz)',
 'data': [50, 35, 4.5, 7, 0, 0, 140, 4, 3, 1, 1, 4, 0, 1, 0, 4, 0, 2]},
{'name':'Banana',
 'Serving Size': '1 medium (126 g/4.5 oz)',
 'data': [110, 0, 0, 0, 0, 0, 450, 13, 30, 10, 3, 12, 19, 1, 2, 15, 0, 2]},
{'name':'Cantaloupe',
 'Serving Size': '1/4 medium (134 g/4.8 oz)',
 'data': [50, 0, 0, 0, 20, 1, 240, 7, 12, 4, 1, 4, 11, 1, 120, 80, 2, 2]},
{'name':'Grapefruit',
 'Serving Size': '1/2 medium (154 g/5.5 oz)',
 'data': [60, 0, 0, 0, 0, 0, 160, 5, 15, 5, 2, 8, 11, 1, 35, 100, 4, 0]},
{'name':'Grapes',
 'Serving Size': '3/4 cup (126 g/4.5 oz)',
 'data': [90, 0, 0, 0, 15, 1, 240, 7, 23, 8, 1, 4, 20, 0, 0, 2, 2, 0]},
{'name':'Honeydew Melon',
 'Serving Size': '1/10 medium melon (134 g/4.8 oz)',
 'data': [50, 0, 0, 0, 30, 1, 210, 6, 12, 4, 1, 4, 11, 1, 2, 45, 2, 2]},
{'name':'Kiwifruit',
 'Serving Size': '2 medium (148 g/5.3 oz)',
 'data': [90, 10, 1, 2, 0, 0, 450, 13, 20, 7, 4, 16, 13, 1, 2, 240, 4, 2]},
{'name':'Lemon',
 'Serving Size': '1 medium (58 g/2.1 oz)',
 'data': [15, 0, 0, 0, 0, 0, 75, 2, 5, 2, 2, 8, 2, 0, 0, 40, 2, 0]},
{'name':'Lime',
 'Serving Size': '1 medium (67 g/2.4 oz)',
 'data': [20, 0, 0, 0, 0, 0, 75, 2, 7, 2, 2, 8, 0, 0, 0, 35, 0, 0]},
{'name':'Nectarine',
 'Serving Size': '1 medium (140 g/5.0 oz)',
 'data': [60, 5, 0.5, 1, 0, 0, 250, 7, 15, 5, 2, 8, 11, 1, 8, 15, 0, 2]},
{'name':'Orange',
 'Serving Size': '1 medium (154 g/5.5 oz)',
 'data': [80, 0, 0, 0, 0, 0, 250, 7, 19, 6, 3, 12, 14, 1, 2, 130, 6, 0]},
{'name':'Peach',
 'Serving Size': '1 medium (147 g/5.3 oz)',
 'data': [60, 0, 0.5, 1, 0, 0, 230, 7, 15, 5, 2, 8, 13, 1, 6, 15, 0, 2]},
{'name':'Pear',
 'Serving Size': '1 medium (166 g/5.9 oz)',
 'data': [100, 0, 0, 0, 0, 0, 190, 5, 26, 9, 6, 24, 16, 1, 0, 10, 2, 0]},
{'name':'Pineapple',
 'Serving Size': '2 slices, 3" diameter, 3/4" thick (112 g/4 oz)',
 'data': [50, 0, 0, 0, 10, 0, 120, 3, 13, 4, 1, 4, 10, 1, 2, 50, 2, 2]},
{'name':'Plums',
 'Serving Size': '2 medium (151 g/5.4 oz)',
 'data': [70, 0, 0, 0, 0, 0, 230, 7, 19, 6, 2, 8, 16, 1, 8, 10, 0, 2]},
{'name':'Strawberries',
 'Serving Size': '8 medium (147 g/5.3 oz)',
 'data': [50, 0, 0, 0, 0, 0, 170, 5, 11, 4, 2, 8, 8, 1, 0, 160, 2, 2]},
{'name':'Sweet Cherries',
 'Serving Size': '21 cherries; 1 cup (140 g/5.0 oz)',
 'data': [100, 0, 0, 0, 0, 0, 350, 10, 26, 9, 1, 4, 16, 1, 2, 15, 2, 2]},
{'name':'Tangerine',
 'Serving Size': '1 medium (109 g/3.9 oz)',
 'data': [50, 0, 0, 0, 0, 0, 160, 5, 13, 4, 2, 8, 9, 1, 6, 45, 4, 0]},
{'name':'Watermelon',
 'Serving Size': '1/18 medium melon; 2 cups diced pieces (280 g/10.0 oz)',
 'data': [80, 0, 0, 0, 0, 0, 270, 8, 21, 7, 1, 4, 20, 1, 30, 25, 2, 4]}]

fruit_data = {}
descriptors_and_units = dict(zip(descriptors, units))
for row in raw_fruit_data:
    fruit_data[row['name']] = {}
    fruit_data[row['name']] = dict({'Serving Size': row['Serving Size']},
            **dict(zip(descriptors_and_units.keys(), row['data'])))

if __name__ == '__main__':

    from kivy.base import runTouchApp

    # All fruit categories will be shown in the left left (first argument),
    # and the first category will be auto-selected -- Melons. So, set the
    # second list to show the melon fruits (second argument).
    runTouchApp(CascadingView(width=800))

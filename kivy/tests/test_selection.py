'''
Selection tests
===============
'''

import unittest

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.listview import ListView
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.adapters.mixins.selection import SelectionObserver, SelectableItem
from kivy.adapters.listadapter import ListAdapter, SelectableListsAdapter, \
        AccumulatingListAdapter


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


class FruitListItem(SelectableItem, Button):
    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = None

    def __init__(self, **kwargs):
        super(FruitListItem, self).__init__(**kwargs)

        # Set deselected_color to be default Button bg color.
        self.deselected_color = self.background_color

    def select(self, *args):
        self.background_color = self.selected_color

    def deselect(self, *args):
        self.background_color = self.deselected_color

    def __repr__(self):
        return self.text


class FruitSelectionObserver(SelectionObserver, Widget):
    fruit_name = StringProperty('')
    call_count = NumericProperty(0)

    def observed_selection_changed(self, list_adapter, selection):
        if len(list_adapter.selection) > 0:
            self.fruit_name = str(list_adapter.selection[0])
        self.call_count += 1


class ListAdapterTestCase(unittest.TestCase):

    def setUp(self):
        self.args_converter = lambda x: {'text': x,
                                         'size_hint_y': None,
                                         'height': 25}

        self.fruits = sorted(fruit_data.keys())

    def test_list_adapter_selection_mode_none(self):
        list_adapter = ListAdapter(self.fruits,
                                   args_converter=self.args_converter,
                                   selection_mode='none',
                                   allow_empty_selection=True,
                                   cls=FruitListItem)

        self.assertEqual(len(list_adapter.selection), 0)
        list_adapter.check_for_empty_selection()
        self.assertEqual(len(list_adapter.selection), 0)

    def test_list_adapter_selection_mode_single(self):
        list_adapter = ListAdapter(self.fruits,
                                   args_converter=self.args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=True,
                                   cls=FruitListItem)

        self.assertEqual(len(list_adapter.selection), 0)
        list_adapter.check_for_empty_selection()
        self.assertEqual(len(list_adapter.selection), 0)
        list_adapter.handle_selection(list_adapter.get_view(0))
        self.assertEqual(len(list_adapter.selection), 1)
        list_adapter.handle_selection(list_adapter.get_view(1))
        self.assertEqual(len(list_adapter.selection), 1)

    def test_list_adapter_selection_mode_single_auto_selection(self):
        list_adapter = ListAdapter(self.fruits,
                                   args_converter=self.args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=FruitListItem)

        self.assertEqual(len(list_adapter.selection), 1)
        list_adapter.check_for_empty_selection()
        self.assertEqual(len(list_adapter.selection), 1)

    def test_list_adapter_selection_mode_multiple_auto_selection(self):
        list_adapter = ListAdapter(self.fruits,
                                   args_converter=self.args_converter,
                                   selection_mode='multiple',
                                   allow_empty_selection=False,
                                   cls=FruitListItem)

        self.assertEqual(len(list_adapter.selection), 1)
        list_adapter.handle_selection(list_adapter.get_view(1))
        self.assertEqual(len(list_adapter.selection), 2)
        list_adapter.handle_selection(list_adapter.get_view(1))
        self.assertEqual(len(list_adapter.selection), 3)

    def test_list_adapter_selection_handle_selection(self):
        list_adapter = ListAdapter(self.fruits,
                                   args_converter=self.args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=FruitListItem)
        selection_observer = FruitSelectionObserver(
                observed_list_adapter=list_adapter)

        list_adapter.handle_selection(list_adapter.get_view(2))
        self.assertEqual(list_adapter.get_view(2).text, 'Banana')
        self.assertEqual(selection_observer.fruit_name, 'Banana')


class SeletableListsAdapterTestCase(unittest.TestCase):

    def setUp(self):
        self.args_converter = lambda x: {'text': x,
                                         'size_hint_y': None,
                                         'height': 25}

        self.fruits = sorted(fruit_data.keys())

    def test_list_adapter_selection_cascade(self):

        # Categories of fruits:
        #
        categories = sorted(fruit_categories.keys())
        fruit_categories_list_adapter = \
            ListAdapter(categories,
                        args_converter=self.args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=FruitListItem)

        fruit_categories_list_view = \
            ListView(adapter=fruit_categories_list_adapter,
                     size_hint=(.2, 1.0))

        # Fruits, for a given category:
        #
        fruits_list_adapter = \
            SelectableListsAdapter(observed_list_adapter=\
                                       fruit_categories_list_adapter,
                                   selectable_lists_dict=fruit_categories,
                                   data=fruit_categories[categories[0]],
                                   args_converter=self.args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=FruitListItem)
        fruits_list_view = ListView(adapter=fruits_list_adapter,
                                    size_hint=(.2, 1.0))

        self.assertEqual(len(fruit_categories_list_adapter.selection), 1)
        self.assertEqual(len(fruits_list_adapter.selection), 1)

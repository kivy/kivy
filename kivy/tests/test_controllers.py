'''
Controller tests
================
'''

import unittest
from random import sample
from random import choice

from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.objectadapter import ObjectAdapter

from kivy.binding import Binding

from kivy.controllers.controller import Controller
from kivy.controllers.objectcontroller import ObjectController
from kivy.controllers.listcontroller import ListController
from kivy.controllers.transformcontroller import TransformController

from kivy.compat import string_types
from kivy.enums import binding_modes
from kivy.enums import binding_transforms
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.models import SelectableDataItem

from kivy.properties import AliasProperty
from kivy.properties import BooleanProperty
from kivy.properties import DictProperty
from kivy.properties import FilterProperty
from kivy.properties import ListProperty
from kivy.properties import MapProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import TransformProperty

from kivy.selection import SelectionTool
from kivy.selection import selection_update_methods
from kivy.selection import selection_schemes

from kivy.uix.label import Label
from kivy.uix.listview import SelectableView
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListItemLabel

from nose.tools import raises


#########################
#  Fruits Example Code

# The following integers_dict and fruit categories / fruit data dictionaries
# are from kivy/examples/widgets/lists/fixtures.py, and the classes are from
# examples there.

# ----------------------------------------------------------------------------
# A dictionary of dicts, with only the minimum required ksel attribute,
# for use with examples using a simple list of integers in a list view.
integers_dict = \
        {str(i): {'text': str(i), 'ksel': SelectionTool(False)} for i in range(100)}


# ----------------------------------------------------------------------------
# A dataset of fruit category and fruit data for use in examples.
#
# Data from http://www.fda.gov/Food/LabelingNutrition/\
#                FoodLabelingGuidanceRegulatoryInformation/\
#                InformationforRestaurantsRetailEstablishments/\
#                ucm063482.htm
#
# Available items for import are:
#
#     fruit_categories
#     fruit_data_attributes
#     fruit_data_attribute_units
#     fruit_data_list_of_dicts
#     fruit_data
#
fruit_categories = \
        {'Melons': {'name': 'Melons',
                    'fruits': ['Cantaloupe', 'Honeydew', 'Watermelon'],
                    'ksel': SelectionTool(False)},
         'Tree Fruits': {'name': 'Tree Fruits',
                         'fruits': ['Apple', 'Avocado', 'Banana', 'Nectarine',
                                    'Peach', 'Pear', 'Pineapple', 'Plum',
                                    'Cherry'],
                         'ksel': SelectionTool(False)},
         'Citrus Fruits': {'name': 'Citrus Fruits',
                           'fruits': ['Grapefruit', 'Lemon', 'Lime', 'Orange',
                                      'Tangerine'],
                           'ksel': SelectionTool(False)},
         'Other Fruits': {'name': 'Other Fruits',
                          'fruits': ['Grape', 'Kiwifruit',
                                     'Strawberry'],
                          'ksel': SelectionTool(False)}}

fruit_data_list_of_dicts = \
    [{'name':'Apple',
      'Serving Size': '1 large (242 g/8 oz)',
      'data': [130, 0, 0, 0, 0, 0, 260, 7, 34, 11, 5, 20, 25, 1, 2, 8, 2, 2],
      'ksel': SelectionTool(False)},
     {'name':'Avocado',
      'Serving Size': '1/5 medium (30 g/1.1 oz)',
      'data': [50, 35, 4.5, 7, 0, 0, 140, 4, 3, 1, 1, 4, 0, 1, 0, 4, 0, 2],
      'ksel': SelectionTool(False)},
     {'name':'Banana',
      'Serving Size': '1 medium (126 g/4.5 oz)',
      'data': [110, 0, 0, 0, 0, 0, 450, 13, 30, 10, 3, 12, 19, 1, 2, 15, 0, 2],
      'ksel': SelectionTool(False)},
     {'name':'Cantaloupe',
      'Serving Size': '1/4 medium (134 g/4.8 oz)',
      'data': [50, 0, 0, 0, 20, 1, 240, 7, 12, 4, 1, 4, 11, 1, 120, 80, 2, 2],
      'ksel': SelectionTool(False)},
     {'name':'Grapefruit',
      'Serving Size': '1/2 medium (154 g/5.5 oz)',
      'data': [60, 0, 0, 0, 0, 0, 160, 5, 15, 5, 2, 8, 11, 1, 35, 100, 4, 0],
      'ksel': SelectionTool(False)},
     {'name':'Grape',
      'Serving Size': '3/4 cup (126 g/4.5 oz)',
      'data': [90, 0, 0, 0, 15, 1, 240, 7, 23, 8, 1, 4, 20, 0, 0, 2, 2, 0],
      'ksel': SelectionTool(False)},
     {'name':'Honeydew',
      'Serving Size': '1/10 medium melon (134 g/4.8 oz)',
      'data': [50, 0, 0, 0, 30, 1, 210, 6, 12, 4, 1, 4, 11, 1, 2, 45, 2, 2],
      'ksel': SelectionTool(False)},
     {'name':'Kiwifruit',
      'Serving Size': '2 medium (148 g/5.3 oz)',
      'data': [90, 10, 1, 2, 0, 0, 450, 13, 20, 7, 4, 16, 13, 1, 2, 240, 4, 2],
      'ksel': SelectionTool(False)},
     {'name':'Lemon',
      'Serving Size': '1 medium (58 g/2.1 oz)',
      'data': [15, 0, 0, 0, 0, 0, 75, 2, 5, 2, 2, 8, 2, 0, 0, 40, 2, 0],
      'ksel': SelectionTool(False)},
     {'name':'Lime',
      'Serving Size': '1 medium (67 g/2.4 oz)',
      'data': [20, 0, 0, 0, 0, 0, 75, 2, 7, 2, 2, 8, 0, 0, 0, 35, 0, 0],
      'ksel': SelectionTool(False)},
     {'name':'Nectarine',
      'Serving Size': '1 medium (140 g/5.0 oz)',
      'data': [60, 5, 0.5, 1, 0, 0, 250, 7, 15, 5, 2, 8, 11, 1, 8, 15, 0, 2],
      'ksel': SelectionTool(False)},
     {'name':'Orange',
      'Serving Size': '1 medium (154 g/5.5 oz)',
      'data': [80, 0, 0, 0, 0, 0, 250, 7, 19, 6, 3, 12, 14, 1, 2, 130, 6, 0],
      'ksel': SelectionTool(False)},
     {'name':'Peach',
      'Serving Size': '1 medium (147 g/5.3 oz)',
      'data': [60, 0, 0.5, 1, 0, 0, 230, 7, 15, 5, 2, 8, 13, 1, 6, 15, 0, 2],
      'ksel': SelectionTool(False)},
     {'name':'Pear',
      'Serving Size': '1 medium (166 g/5.9 oz)',
      'data': [100, 0, 0, 0, 0, 0, 190, 5, 26, 9, 6, 24, 16, 1, 0, 10, 2, 0],
      'ksel': SelectionTool(False)},
     {'name':'Pineapple',
      'Serving Size': '2 slices, 3" diameter, 3/4" thick (112 g/4 oz)',
      'data': [50, 0, 0, 0, 10, 0, 120, 3, 13, 4, 1, 4, 10, 1, 2, 50, 2, 2],
      'ksel': SelectionTool(False)},
     {'name':'Plum',
      'Serving Size': '2 medium (151 g/5.4 oz)',
      'data': [70, 0, 0, 0, 0, 0, 230, 7, 19, 6, 2, 8, 16, 1, 8, 10, 0, 2],
      'ksel': SelectionTool(False)},
     {'name':'Strawberry',
      'Serving Size': '8 medium (147 g/5.3 oz)',
      'data': [50, 0, 0, 0, 0, 0, 170, 5, 11, 4, 2, 8, 8, 1, 0, 160, 2, 2],
      'ksel': SelectionTool(False)},
     {'name':'Cherry',
      'Serving Size': '21 cherries; 1 cup (140 g/5.0 oz)',
      'data': [100, 0, 0, 0, 0, 0, 350, 10, 26, 9, 1, 4, 16, 1, 2, 15, 2, 2],
      'ksel': SelectionTool(False)},
     {'name':'Tangerine',
      'Serving Size': '1 medium (109 g/3.9 oz)',
      'data': [50, 0, 0, 0, 0, 0, 160, 5, 13, 4, 2, 8, 9, 1, 6, 45, 4, 0],
      'ksel': SelectionTool(False)},
     {'name':'Watermelon',
      'Serving Size': '1/18 medium melon; 2 cups diced pieces (280 g/10.0 oz)',
      'data': [80, 0, 0, 0, 0, 0, 270, 8, 21, 7, 1, 4, 20, 1, 30, 25, 2, 4],
      'ksel': SelectionTool(False)}]


fruit_data_attributes = ['(gram weight/ ounce weight)',
                         'Calories',
                         'Calories from Fat',
                         'Total Fat',
                         'Sodium',
                         'Potassium',
                         'Total Carbo-hydrate',
                         'Dietary Fiber',
                         'Sugars',
                         'Protein',
                         'Vitamin A',
                         'Vitamin C',
                         'Calcium',
                         'Iron']


fruit_data_attribute_units = ['(g)',
                              '(%DV)',
                              '(mg)',
                              '(%DV)',
                              '(mg)',
                              '(%DV)',
                              '(g)',
                              '(%DV)',
                              '(g)(%DV)',
                              '(g)',
                              '(g)',
                              '(%DV)',
                              '(%DV)',
                              '(%DV)',
                              '(%DV)']

attributes_and_units = \
        dict(list(zip(fruit_data_attributes, fruit_data_attribute_units)))

fruit_data = {}
for fruit_record in fruit_data_list_of_dicts:
    fruit_data[fruit_record['name']] = {}
    fruit_data[fruit_record['name']] = \
            dict({'name': fruit_record['name'],
                  'Serving Size': fruit_record['Serving Size'],
                  'ksel': SelectionTool(False)},
            **dict(list(zip(list(attributes_and_units.keys()),
                            fruit_record['data']))))


class CategoryItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(CategoryItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.fruits = kwargs.get('fruits', [])


class FruitItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')
        self.data = kwargs.get('data', [])

    def size(self):
        return self.data[0]


def reset_to_defaults(db_dict):
    for key in db_dict:
        db_dict[key]['ksel'].deselect()

category_data_items = \
    [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]

fruit_data_items = \
    [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]


class FruitsListController(ListController):

    def __init__(self, **kwargs):
        super(FruitsListController, self).__init__(**kwargs)

    def fruit_category_changed(self, fruit_categories_controller, *args):
        if len(fruit_categories_controller.selection) == 0:
            self.data = []
            return

        category = \
                fruit_categories[str(fruit_categories_controller.selection[0])]

        self.data = \
            [f for f in fruit_data_items if f.name in category['fruits']]


##################################
#  Phonetic Alphabet Example Code


class CustomDataItem(SelectableDataItem):

    def __init__(self, **kwargs):
        super(CustomDataItem, self).__init__(**kwargs)
        self.text = kwargs.get('text', '')
        self.ksel = SelectionTool(False)


class PhoneticItem(SelectableView, Label):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(PhoneticItem, self).__init__(**kwargs)


# NATO alphabet words
phonetic_string_data = [
    'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf',
    'Hotel', 'India', 'Juliet', 'Kilo', 'Lima', 'Mike', 'November',
    'Oscar', 'Papa', 'Quebec', 'Romeo', 'Sierra', 'Tango', 'Uniform',
    'Victor', 'Whiskey', 'X-ray', 'Yankee', 'Zulu']

phonetic_string_data_subset = [
    'Delta', 'Oscar', 'Golf', 'Sierra',
    'Alpha', 'November', 'Delta',
    'Charlie', 'Alpha', 'Tango', 'Sierra']


class PhoneticAlphabetcontroller(ListController):

    object_data = ListProperty([])

    def create_list_item_obj(self):
        return CustomDataItem(text=choice(self.nato_alphabet_words))

    def create_list_item_obj_list(self, n):
        return [CustomDataItem(text=choice(self.nato_alphabet_words))] * n


class FruitcontrollersTestCase(unittest.TestCase):

    def setUp(self):

        self.integers_dict = \
         {str(i): {'text': str(i), 'ksel': SelectionTool(False)} for i in range(100)}

        reset_to_defaults(fruit_data)

    def test_instantiating_an_controller_with_no_data(self):
        # with no data
        controller = Controller()

        self.assertIsNotNone(controller)

    def test_simple_list_controller_methods(self):
        list_controller = ListController(data=['cat', 'dog'])
        self.assertEqual(list_controller.get_count(), 2)
        self.assertEqual(list_controller.get_selectable_item(0), 'cat')
        self.assertEqual(list_controller.get_selectable_item(1), 'dog')

    def test_instantiating_list_controller(self):
        list_controller = ListController(data=['cat', 'dog'])

        self.assertEqual([obj for obj in list_controller.data],
                         ['cat', 'dog'])
        self.assertEqual(list_controller.get_count(), 2)

        cat_data_item = list_controller.get_selectable_item(0)
        self.assertEqual(cat_data_item, 'cat')
        self.assertTrue(isinstance(cat_data_item, string_types))

    def test_list_controller_selection_mode_single(self):
        fruit_data_items[0].ksel.select()

        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='single',
                                   allow_empty_selection=False)

        self.assertEqual(sorted([obj.name for obj in list_controller.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        apple_data_item = list_controller.get_selectable_item(0)
        self.assertTrue(isinstance(apple_data_item, FruitItem))
        self.assertTrue(isinstance(apple_data_item, SelectableDataItem))
        self.assertTrue(apple_data_item.ksel.is_selected())

    def test_list_controller_with_dict_data(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        letters_dicts = \
           [{'text': l, 'ksel': SelectionTool(False)} for l in alphabet]

        letters_dicts[0]['ksel'].select()

        list_controller = ListController(data=letters_dicts,
                                   selection_mode='single',
                                   allow_empty_selection=False)

        apple_data_item = list_controller.get_selectable_item(0)
        self.assertTrue(isinstance(apple_data_item, dict))
        self.assertTrue(apple_data_item['ksel'].is_selected())

    def test_list_controller_with_custom_data_item_class(self):

        class DataItem(object):
            def __init__(self, text=''):
                self.text = text
                self.ksel = SelectionTool(False)

        data_items = []
        data_items.append(DataItem(text='cat'))
        data_items.append(DataItem(text='dog'))
        data_items.append(DataItem(text='frog'))

        list_controller = ListController(data=data_items,
                                   selection_mode='single',
                                   allow_empty_selection=False)

        data_item = list_controller.get_selectable_item(0)
        self.assertTrue(isinstance(data_item, DataItem))
        self.assertTrue(data_item.ksel.is_selected())

    def test_list_controller_with_widget_as_data_item_class(self):

        # Use a widget as data item.
        class LabelItem(Label):
            text = StringProperty('')

            def __init__(self, text):
                self.text = text
                self.ksel = SelectionTool(False)

        class LabelItemWithMethod(LabelItem):

            def __init__(self, text):
                self.text = text
                self.ksel = SelectionTool(False)

        class PlainLabelItem(Label):
            text = StringProperty('')

        data_items = []
        data_items.append(LabelItem(text='cat'))
        data_items.append(LabelItemWithMethod(text='dog'))
        data_items.append(PlainLabelItem(text='frog'))

        list_controller = ListController(data=data_items,
                                   selection_mode='single',
                                   allow_empty_selection=True)

        label_item = list_controller.get_selectable_item(0)
        self.assertTrue(isinstance(label_item, LabelItem))
        self.assertFalse(label_item.ksel.is_selected())

        data_item = list_controller.get_selectable_item(1)
        self.assertTrue(isinstance(data_item, LabelItemWithMethod))
        self.assertFalse(data_item.ksel.is_selected())

    def test_list_controller_selection_mode_none(self):

        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='none',
                                   allow_empty_selection=True)

        self.assertEqual(sorted([obj.name for obj in list_controller.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        apple_data_item = list_controller.get_selectable_item(0)
        self.assertTrue(isinstance(apple_data_item, FruitItem))

    def test_list_controller_selection_mode_multiple_select_list(self):

        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='multiple',
                                   allow_empty_selection=True)

        items = []
        items.append(list_controller.get_selectable_item(0))
        items.append(list_controller.get_selectable_item(1))
        items.append(list_controller.get_selectable_item(2))

        self.assertEqual(len(items), 3)
        list_controller.select_list(items)
        self.assertEqual(len(list_controller.selection), 3)

        items = []
        items.append(list_controller.get_selectable_item(3))
        items.append(list_controller.get_selectable_item(4))
        items.append(list_controller.get_selectable_item(5))

        self.assertEqual(len(items), 3)
        list_controller.select_list(items)
        self.assertEqual(len(list_controller.selection), 6)

        items = []
        items.append(list_controller.get_selectable_item(0))
        items.append(list_controller.get_selectable_item(1))
        items.append(list_controller.get_selectable_item(2))

        self.assertEqual(len(items), 3)
        list_controller.select_list(items, extend=False)
        self.assertEqual(len(list_controller.selection), 3)

        list_controller.deselect_list(items)
        self.assertEqual(len(list_controller.selection), 0)

    def test_list_controller_with_dicts_as_data(self):
        bare_minimum_dicts = \
            [{'text': str(i), 'ksel': SelectionTool(False)} for i in range(100)]

        list_controller = ListController(data=bare_minimum_dicts,
                                   selection_mode='none',
                                   allow_empty_selection=True)

        self.assertEqual([rec['text'] for rec in list_controller.data],
            [str(i) for i in range(100)])

        data_item = list_controller.get_selectable_item(0)
        self.assertTrue(type(data_item), dict)

        # Utility calls for coverage:

        self.assertEqual(list_controller.get_count(), 100)

    def test_list_controller_with_dicts_as_data_multiple_selection(self):
        bare_minimum_dicts = \
            [{'text': str(i), 'ksel': SelectionTool(False)} for i in range(100)]

        list_controller = ListController(data=bare_minimum_dicts,
                                   selection_mode='multiple',
                                   allow_empty_selection=False)

        self.assertEqual([rec['text'] for rec in list_controller.data],
            [str(i) for i in range(100)])

        for i in range(50):
            list_controller.handle_selection(list_controller.get_selectable_item(i))

        self.assertEqual(len(list_controller.selection), 50)

        # This is for code coverage:
        list_controller.selection_mode = 'none'
        list_controller.handle_selection(list_controller.get_selectable_item(25))
        list_controller.selection_mode = 'single'
        list_controller.handle_selection(list_controller.get_selectable_item(24))
        list_controller.handle_selection(list_controller.get_selectable_item(24))

    def test_list_controller_bindings(self):

        fruit_categories_list_controller = \
            ListController(data=category_data_items,
                        selection_mode='single',
                        allow_empty_selection=False)

        first_category_fruits = \
            fruit_categories[list(fruit_categories.keys())[0]]['fruits']

        first_category_fruit_data_items = \
            [f for f in fruit_data_items if f.name in first_category_fruits]

        fruits_list_controller = \
                FruitsListController(data=first_category_fruit_data_items,
                                  selection_mode='single',
                                  allow_empty_selection=False)

        fruit_categories_list_controller.bind(
            on_selection_change=fruits_list_controller.fruit_category_changed)

    def test_list_controller_operations_trimming(self):

        class LetterItem(object):
            def __init__(self, text):
                self.text = text
                self.ksel = SelectionTool(False)

        alphabet = [l for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']

        # trim right of sel

        alphabet_controller = ListController(
                        data=[LetterItem(l) for l in alphabet],
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True)

        a_item = alphabet_controller.get_selectable_item(0)
        self.assertEqual(a_item.text, 'A')

        alphabet_controller.handle_selection(a_item)
        self.assertEqual(len(alphabet_controller.selection), 1)
        self.assertTrue(a_item.ksel.is_selected())

        alphabet_controller.trim_right_of_sel()
        self.assertEqual(len(alphabet_controller.data), 1)

        # trim left of sel

        alphabet_controller = ListController(
                        data=[LetterItem(l) for l in alphabet],
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True)

        z_item = alphabet_controller.get_selectable_item(25)
        self.assertEqual(z_item.text, 'Z')

        alphabet_controller.handle_selection(z_item)
        self.assertEqual(len(alphabet_controller.selection), 1)
        self.assertTrue(z_item.ksel.is_selected())

        alphabet_controller.trim_left_of_sel()
        self.assertEqual(len(alphabet_controller.data), 1)

        # trim to sel

        alphabet_controller = ListController(
                        data=[LetterItem(l) for l in alphabet],
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True)

        g_item = alphabet_controller.get_selectable_item(6)
        self.assertEqual(g_item.text, 'G')
        alphabet_controller.handle_selection(g_item)

        m_item = alphabet_controller.get_selectable_item(12)
        self.assertEqual(m_item.text, 'M')
        alphabet_controller.handle_selection(m_item)

        alphabet_controller.trim_to_sel()
        self.assertEqual(len(alphabet_controller.data), 7)

        # cut to sel

        alphabet_controller = ListController(
                        data=[LetterItem(l) for l in alphabet],
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True)

        g_item = alphabet_controller.get_selectable_item(6)
        self.assertEqual(g_item.text, 'G')
        alphabet_controller.handle_selection(g_item)

        m_item = alphabet_controller.get_selectable_item(12)
        self.assertEqual(m_item.text, 'M')
        alphabet_controller.handle_selection(m_item)

        alphabet_controller.cut_to_sel()
        self.assertEqual(len(alphabet_controller.data), 2)

    def test_list_controller_reset_data(self):
        class PetListener(object):
            def __init__(self, pet):
                self.current_pet = pet

            # This should happen as a result of data changing.
            def callback(self, *args):
                self.current_pet = args[1]

        pet_listener = PetListener('cat')

        list_controller = ListController(
                        data=['cat'],
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True)

        list_controller.bind(data=pet_listener.callback)

        self.assertEqual(pet_listener.current_pet, 'cat')
        dog_data = ['dog']
        list_controller.data = dog_data
        self.assertEqual(list_controller.data, ['dog'])
        self.assertEqual(pet_listener.current_pet, dog_data)

        # Now just change an item.
        list_controller.data[0] = 'cat'
        self.assertEqual(list_controller.data, ['cat'])
        self.assertEqual(pet_listener.current_pet, ['cat'])


class OpObservableListOpsTestCase(unittest.TestCase):

    def setUp(self):

        self.list_controller = ListController(
                data=[PhoneticItem(text=p) for p in phonetic_string_data_subset],
                selection_mode='single',
                allow_empty_selection=False)

    def test_OOL_setitem_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        before = self.list_controller.get_selectable_item(sel_index)
        self.list_controller.data[sel_index] = PhoneticItem(text=choice(phonetic_string_data))
        after = self.list_controller.get_selectable_item(sel_index)
        # The item should be a new object.
        self.assertNotEqual(before, after)
        # The new item should not be selected.
        self.assertFalse(after.ksel.is_selected())

    def test_OOL_delitem_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        del self.list_controller.data[sel_index]

    def test_OOL_setslice_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        self.list_controller.data[sel_index:sel_index + 3] = \
                [PhoneticItem(text=choice(phonetic_string_data))] * 3

    def test_OOL_delslice_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        del self.list_controller.data[sel_index:sel_index + 3]

    def test_OOL_append_op(self):
        self.list_controller.data.append(PhoneticItem(text=choice(phonetic_string_data)))

    def test_OOL_remove_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        sel_obj = self.list_controller.data[sel_index]
        self.list_controller.data.remove(sel_obj)

    def test_OOL_insert_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        self.list_controller.data.insert(
                sel_index,
                PhoneticItem(text=choice(phonetic_string_data)))

    def test_OOL_pop_op(self):
        self.list_controller.data.pop()

    def test_OOL_pop_i_op(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        self.list_controller.data.pop(sel_index)

    def test_OOL_extend_op(self):
        self.list_controller.data.extend([PhoneticItem(text=choice(phonetic_string_data))] * 3)

    def test_OOL_sort_op(self):
        self.list_controller.data.sort()

    def test_OOL_reverse_op(self):
        self.list_controller.data.reverse()

class ListControllerInteroperabilityTestCase(unittest.TestCase):

    def setUp(self):

        class FruitsController(ListController):

            small_fruits = FilterProperty(lambda item: item.size() < 40)
            medium_fruits = FilterProperty(lambda item: 40 <= item.size() < 80)
            large_fruits = FilterProperty(lambda item: item.size() >= 80)

        self.fruits_controller = FruitsController(data=fruit_data_items,
                                                  selection_mode='multiple')

    def test_list_controller_filter_properties(self):

        self.assertEqual(sorted(fruit_data_items),
                         (sorted(self.fruits_controller.small_fruits
                             + self.fruits_controller.medium_fruits
                             + self.fruits_controller.large_fruits)))

    def test_list_controller_selection_as_filter_property(self):

        self.fruits_controller.selection = self.fruits_controller.small_fruits
        self.assertEqual(self.fruits_controller.selection,
                         self.fruits_controller.small_fruits)

        self.fruits_controller.selection = self.fruits_controller.medium_fruits
        self.assertEqual(self.fruits_controller.selection,
                         self.fruits_controller.medium_fruits)

        self.fruits_controller.selection = self.fruits_controller.large_fruits
        self.assertEqual(self.fruits_controller.selection,
                         self.fruits_controller.large_fruits)

    def test_list_controller_interoperating_with_adapters(self):

        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        self.fruits = ListController(
                data=fruit_data_items,
                allow_empty_selection=False)

        self.fruit_categories = ListController(
                data=category_data_items,
                allow_empty_selection=False)

        self.fruit_categories_list_adapter = ListAdapter(
                data=Binding(source=self.fruit_categories, prop='data'),
                args_converter=list_item_args_converter,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)

        self.current_category_view = ObjectController(
                data=Binding(source=self.fruit_categories_list_adapter,
                             prop='selection',
                             mode=binding_modes.FIRST_ITEM))

        self.current_category = TransformController(
                data=Binding(source=self.current_category_view,
                             prop='data',
                             transform=lambda v: category_data_items[v.index]))

        def fruits_for_category(category):
            # TODO: The lambda commented out below has the reference to
            #       App.app().current_category.data.fruits inside a list
            #       comprehension, which results in repeated calls. Here we do
            #       the call once, and use the result in the comprehension.
            #       Also tried the lambda with a generator.
            cat_fruits = self.current_category.data.fruits
            return [f for f in fruit_data_items if f.name in cat_fruits]

        self.category_fruits = TransformController(
                data=Binding(source=self.current_category,
                             prop='data',
                             transform=(binding_transforms.TRANSFORM, fruits_for_category)))
                                 #lambda fruits: [f for f in App.app().fruits.data if f.name in App.app().current_category.data.fruits])))

        self.current_fruits_adapter = ListAdapter(
                data=Binding(source=self.category_fruits, prop='data'),
                args_converter=list_item_args_converter,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)

        self.current_fruit = TransformController(
                data=Binding(source=self.current_fruits_adapter,
                             prop='selection',
                             mode=binding_modes.FIRST_ITEM,
                             transform=(binding_transforms.TRANSFORM,
                                        lambda v: self.current_fruits_adapter.data[v.index])))

        self.current_fruit_adapter = ObjectAdapter(
                data=Binding(source=self.current_fruit,
                             prop='data'),
                args_converter=lambda row_index, fruit: {'text': fruit.name},
                cls=ListItemLabel)

        grapefruit_view_item = self.current_fruit_adapter.get_view(0)
        self.assertEqual(grapefruit_view_item.text, 'Grapefruit')

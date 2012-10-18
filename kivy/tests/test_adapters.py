'''
Adapter tests
=============
'''

import unittest

from kivy.uix.listview import ListItemButton
from kivy.uix.label import Label
from kivy.adapters.adapter import Adapter
from kivy.adapters.listadapter import SimpleListAdapter
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.mixins.selection import SelectableDataItem
from kivy.lang import Builder

from nose.tools import raises


# The following integers_dict and fruit categories / fruit data dictionaries
# are from kivy/examples/widgets/lists/fixtures.py, and the classes are from
# examples there.

# ----------------------------------------------------------------------------
# A dictionary of dicts, with only the minimum required is_selected attribute,
# for use with examples using a simple list of integers in a list view.
integers_dict = \
        {str(i): {'text': str(i), 'is_selected': False} for i in xrange(100)}


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
                    'is_selected': False},
         'Tree Fruits': {'name': 'Tree Fruits',
                         'fruits': ['Apple', 'Avocado', 'Banana', 'Nectarine',
                                    'Peach', 'Pear', 'Pineapple', 'Plum',
                                    'Cherry'],
                         'is_selected': False},
         'Citrus Fruits': {'name': 'Citrus Fruits',
                           'fruits': ['Grapefruit', 'Lemon', 'Lime', 'Orange',
                                      'Tangerine'],
                           'is_selected': False},
         'Other Fruits': {'name': 'Other Fruits',
                          'fruits': ['Grape', 'Kiwifruit',
                                     'Strawberry'],
                          'is_selected': False}}

fruit_data_list_of_dicts = \
    [{'name':'Apple',
      'Serving Size': '1 large (242 g/8 oz)',
      'data': [130, 0, 0, 0, 0, 0, 260, 7, 34, 11, 5, 20, 25, 1, 2, 8, 2, 2],
      'is_selected': False},
     {'name':'Avocado',
      'Serving Size': '1/5 medium (30 g/1.1 oz)',
      'data': [50, 35, 4.5, 7, 0, 0, 140, 4, 3, 1, 1, 4, 0, 1, 0, 4, 0, 2],
      'is_selected': False},
     {'name':'Banana',
      'Serving Size': '1 medium (126 g/4.5 oz)',
      'data': [110, 0, 0, 0, 0, 0, 450, 13, 30, 10, 3, 12, 19, 1, 2, 15, 0, 2],
      'is_selected': False},
     {'name':'Cantaloupe',
      'Serving Size': '1/4 medium (134 g/4.8 oz)',
      'data': [50, 0, 0, 0, 20, 1, 240, 7, 12, 4, 1, 4, 11, 1, 120, 80, 2, 2],
      'is_selected': False},
     {'name':'Grapefruit',
      'Serving Size': '1/2 medium (154 g/5.5 oz)',
      'data': [60, 0, 0, 0, 0, 0, 160, 5, 15, 5, 2, 8, 11, 1, 35, 100, 4, 0],
      'is_selected': False},
     {'name':'Grape',
      'Serving Size': '3/4 cup (126 g/4.5 oz)',
      'data': [90, 0, 0, 0, 15, 1, 240, 7, 23, 8, 1, 4, 20, 0, 0, 2, 2, 0],
      'is_selected': False},
     {'name':'Honeydew',
      'Serving Size': '1/10 medium melon (134 g/4.8 oz)',
      'data': [50, 0, 0, 0, 30, 1, 210, 6, 12, 4, 1, 4, 11, 1, 2, 45, 2, 2],
      'is_selected': False},
     {'name':'Kiwifruit',
      'Serving Size': '2 medium (148 g/5.3 oz)',
      'data': [90, 10, 1, 2, 0, 0, 450, 13, 20, 7, 4, 16, 13, 1, 2, 240, 4, 2],
      'is_selected': False},
     {'name':'Lemon',
      'Serving Size': '1 medium (58 g/2.1 oz)',
      'data': [15, 0, 0, 0, 0, 0, 75, 2, 5, 2, 2, 8, 2, 0, 0, 40, 2, 0],
      'is_selected': False},
     {'name':'Lime',
      'Serving Size': '1 medium (67 g/2.4 oz)',
      'data': [20, 0, 0, 0, 0, 0, 75, 2, 7, 2, 2, 8, 0, 0, 0, 35, 0, 0],
      'is_selected': False},
     {'name':'Nectarine',
      'Serving Size': '1 medium (140 g/5.0 oz)',
      'data': [60, 5, 0.5, 1, 0, 0, 250, 7, 15, 5, 2, 8, 11, 1, 8, 15, 0, 2],
      'is_selected': False},
     {'name':'Orange',
      'Serving Size': '1 medium (154 g/5.5 oz)',
      'data': [80, 0, 0, 0, 0, 0, 250, 7, 19, 6, 3, 12, 14, 1, 2, 130, 6, 0],
      'is_selected': False},
     {'name':'Peach',
      'Serving Size': '1 medium (147 g/5.3 oz)',
      'data': [60, 0, 0.5, 1, 0, 0, 230, 7, 15, 5, 2, 8, 13, 1, 6, 15, 0, 2],
      'is_selected': False},
     {'name':'Pear',
      'Serving Size': '1 medium (166 g/5.9 oz)',
      'data': [100, 0, 0, 0, 0, 0, 190, 5, 26, 9, 6, 24, 16, 1, 0, 10, 2, 0],
      'is_selected': False},
     {'name':'Pineapple',
      'Serving Size': '2 slices, 3" diameter, 3/4" thick (112 g/4 oz)',
      'data': [50, 0, 0, 0, 10, 0, 120, 3, 13, 4, 1, 4, 10, 1, 2, 50, 2, 2],
      'is_selected': False},
     {'name':'Plum',
      'Serving Size': '2 medium (151 g/5.4 oz)',
      'data': [70, 0, 0, 0, 0, 0, 230, 7, 19, 6, 2, 8, 16, 1, 8, 10, 0, 2],
      'is_selected': False},
     {'name':'Strawberry',
      'Serving Size': '8 medium (147 g/5.3 oz)',
      'data': [50, 0, 0, 0, 0, 0, 170, 5, 11, 4, 2, 8, 8, 1, 0, 160, 2, 2],
      'is_selected': False},
     {'name':'Cherry',
      'Serving Size': '21 cherries; 1 cup (140 g/5.0 oz)',
      'data': [100, 0, 0, 0, 0, 0, 350, 10, 26, 9, 1, 4, 16, 1, 2, 15, 2, 2],
      'is_selected': False},
     {'name':'Tangerine',
      'Serving Size': '1 medium (109 g/3.9 oz)',
      'data': [50, 0, 0, 0, 0, 0, 160, 5, 13, 4, 2, 8, 9, 1, 6, 45, 4, 0],
      'is_selected': False},
     {'name':'Watermelon',
      'Serving Size': '1/18 medium melon; 2 cups diced pieces (280 g/10.0 oz)',
      'data': [80, 0, 0, 0, 0, 0, 270, 8, 21, 7, 1, 4, 20, 1, 30, 25, 2, 4],
      'is_selected': False}]

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
        dict(zip(fruit_data_attributes, fruit_data_attribute_units))

fruit_data = {}
for fruit_record in fruit_data_list_of_dicts:
    fruit_data[fruit_record['name']] = {}
    fruit_data[fruit_record['name']] = \
            dict({'name': fruit_record['name'],
                  'Serving Size': fruit_record['Serving Size'],
                  'is_selected': fruit_record['is_selected']},
            **dict(zip(attributes_and_units.keys(), fruit_record['data'])))


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


def reset_to_defaults(db_dict):
    for key in db_dict:
        db_dict[key]['is_selected'] = False

category_data_items = \
    [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]

fruit_data_items = \
    [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]


class FruitsListAdapter(ListAdapter):

    def __init__(self, **kwargs):
        kwargs['args_converter'] = lambda rec: {'text': rec['name'],
                                               'size_hint_y': None,
                                               'height': 25}
        super(FruitsListAdapter, self).__init__(**kwargs)

    def fruit_category_changed(self, fruit_categories_adapter, *args):
        if len(fruit_categories_adapter.selection) == 0:
            self.data = []
            return

        category = \
                fruit_categories[str(fruit_categories_adapter.selection[0])]

        self.data = \
            [f for f in fruit_data_items if f.name in category['fruits']]


Builder.load_string('''
[CustomListItem@SelectableView+BoxLayout]:
    index: ctx.index
    size_hint_y: ctx.size_hint_y
    height: ctx.height
    is_selected: ctx.is_selected
    ListItemButton:
        index: ctx.index
        text: ctx.text
        is_selected: ctx.is_selected
''')


class AdaptersTestCase(unittest.TestCase):

    def setUp(self):
        self.args_converter = lambda rec: {'text': rec['name'],
                                           'size_hint_y': None,
                                           'height': 25}

        reset_to_defaults(fruit_data)

    def test_list_adapter_selection_mode_none(self):
        list_adapter = ListAdapter(data=fruit_data_items,
                                   args_converter=self.args_converter,
                                   selection_mode='none',
                                   allow_empty_selection=True,
                                   cls=ListItemButton)

        self.assertEqual(sorted([obj.name for obj in list_adapter.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter, self.args_converter)
        self.assertEqual(list_adapter.template, None)

        apple_data_item = list_adapter.get_item(0)
        self.assertTrue(isinstance(apple_data_item, FruitItem))

    def test_list_adapter_with_dicts_as_data(self):
        bare_minimum_dicts = \
            [{'text': str(i), 'is_selected': False} for i in xrange(100)]

        args_converter = lambda rec: {'text': rec['text'],
                                      'size_hint_y': None,
                                      'height': 25}

        list_adapter = ListAdapter(data=bare_minimum_dicts,
                                   args_converter=args_converter,
                                   selection_mode='none',
                                   allow_empty_selection=True,
                                   cls=ListItemButton)

        self.assertEqual([rec['text'] for rec in list_adapter.data],
            [str(i) for i in xrange(100)])

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter, args_converter)

        data_item = list_adapter.get_item(0)
        self.assertTrue(type(data_item), dict)

    def test_list_adapter_bindings(self):
        list_item_args_converter = \
                lambda selectable: {'text': selectable.name,
                                    'size_hint_y': None,
                                    'height': 25}

        fruit_categories_list_adapter = \
            ListAdapter(data=category_data_items,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        first_category_fruits = \
            fruit_categories[fruit_categories.keys()[0]]['fruits']

        first_category_fruit_data_items = \
            [f for f in fruit_data_items if f.name in first_category_fruits]

        fruits_list_adapter = \
                FruitsListAdapter(data=first_category_fruit_data_items,
                                  args_converter=list_item_args_converter,
                                  selection_mode='single',
                                  allow_empty_selection=False,
                                  cls=ListItemButton)

        fruit_categories_list_adapter.bind(
            on_selection_change=fruits_list_adapter.fruit_category_changed)

    def test_instantiating_adapters_with_both_cls_and_template(self):
        list_item_args_converter = \
                lambda rec: {'text': rec['text'],
                             'is_selected': rec['is_selected'],
                             'size_hint_y': None,
                             'height': 25}

        # First, for a plain Adapter:
        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(args_converter=list_item_args_converter,
                        template='CustomListItem',
                        cls=ListItemButton)

        msg = 'Cannot use cls and template at the same time'
        self.assertEqual(str(cm.exception), msg)

        # And now for a ListAdapter:
        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                ListAdapter(data=category_data_items,
                            args_converter=list_item_args_converter,
                            selection_mode='single',
                            allow_empty_selection=False,
                            template='CustomListItem',
                            cls=ListItemButton)

        msg = 'Cannot use cls and template at the same time'
        self.assertEqual(str(cm.exception), msg)

    def test_view_from_adapter(self):
        list_item_args_converter = \
                lambda selectable: {'text': selectable.name,
                                    'size_hint_y': None,
                                    'height': 25}

        fruit_categories_list_adapter = \
            ListAdapter(data=category_data_items,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        view = fruit_categories_list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))

    @raises(Exception)
    def test_instantiating_an_adapter_with_neither_cls_nor_template(self):
        def dummy_converter():
            pass

        fruit_categories_list_adapter = \
            Adapter(args_converter=dummy_converter)

    def test_instantiating_an_adapter_with_neither_cls_nor_template(self):
        def dummy_converter():
            pass

        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(args_converter=dummy_converter)

        msg = 'A cls or template must be defined'
        self.assertEqual(str(cm.exception), msg)

    def test_instantiating_list_adapter_with_kwargs(self):
        from kivy.adapters.args_converters import list_item_args_converter

        def dummy_converter():
            pass

        class Adapter_1(Adapter):
            def __init__(self, **kwargs):
                kwargs['args_converter'] = dummy_converter
                super(Adapter_1, self).__init__(**kwargs)

        kwargs = {}
        kwargs['args_converter'] = dummy_converter
        kwargs['cls'] = ListItemButton

        my_adapter = Adapter(**kwargs)
        self.assertEqual(my_adapter.args_converter, dummy_converter)

        my_adapter = Adapter_1(**kwargs)
        self.assertEqual(my_adapter.args_converter, dummy_converter)

        kwargs_2 = {}
        kwargs_2['cls'] = ListItemButton

        adapter_2 = Adapter(**kwargs_2)
        self.assertEqual(adapter_2.args_converter, list_item_args_converter)

    def test_instantiating_simple_list_adapter(self):
        # with no data
        with self.assertRaises(Exception) as cm:
            simple_list_adapter = SimpleListAdapter()

        msg = 'list adapter: input must include data argument'
        self.assertEqual(str(cm.exception), msg)

        # with data of wrong type
        with self.assertRaises(Exception) as cm:
            simple_list_adapter = SimpleListAdapter(data=dict)

        msg = 'list adapter: data must be a tuple or list'
        self.assertEqual(str(cm.exception), msg)

    def test_simple_list_adapter_methods(self):
        simple_list_adapter = SimpleListAdapter(data=['cat', 'dog'],
                                                cls=Label)
        self.assertEqual(simple_list_adapter.get_count(), 2)
        self.assertEqual(simple_list_adapter.get_item(0), 'cat')
        self.assertEqual(simple_list_adapter.get_item(1), 'dog')
        self.assertIsNone(simple_list_adapter.get_item(-1))
        self.assertIsNone(simple_list_adapter.get_item(2))

        view = simple_list_adapter.get_view(0)
        self.assertTrue(isinstance(view, Label))
        self.assertIsNone(simple_list_adapter.get_view(-1))
        self.assertIsNone(simple_list_adapter.get_view(2))

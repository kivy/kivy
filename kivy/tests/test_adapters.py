'''
Adapter tests
=============
'''

import unittest

from kivy.uix.listview import SelectableView
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListItemLabel
from kivy.uix.listview import CompositeListItem
from kivy.uix.label import Label

from kivy.adapters.models import SelectableDataItem
from kivy.adapters.adapter import Adapter
from kivy.adapters.simplelistadapter import SimpleListAdapter
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.dictadapter import DictAdapter

from kivy.properties import BooleanProperty
from kivy.properties import StringProperty

from kivy.factory import Factory
from kivy.lang import Builder
from kivy.compat import string_types

from nose.tools import raises


# The following integers_dict and fruit categories / fruit data dictionaries
# are from kivy/examples/widgets/lists/fixtures.py, and the classes are from
# examples there.

# ----------------------------------------------------------------------------
# A dictionary of dicts, with only the minimum required is_selected attribute,
# for use with examples using a simple list of integers in a list view.
integers_dict = \
        {str(i): {'text': str(i), 'is_selected': False} for i in range(100)}


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
        dict(list(zip(fruit_data_attributes, fruit_data_attribute_units)))

fruit_data = {}
for fruit_record in fruit_data_list_of_dicts:
    fruit_data[fruit_record['name']] = {}
    fruit_data[fruit_record['name']] = \
            dict({'name': fruit_record['name'],
                  'Serving Size': fruit_record['Serving Size'],
                  'is_selected': fruit_record['is_selected']},
            **dict(list(zip(list(attributes_and_units.keys()),
                            fruit_record['data']))))


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
        kwargs['args_converter'] = \
                lambda row_index, selectable: {'text': selectable.name,
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


# [TODO] Needed if setup.py run normally, after merge to master?
Factory.register('SelectableView', cls=SelectableView)
Factory.register('ListItemButton', cls=ListItemButton)

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

Builder.load_string('''
[CustomSimpleListItem@SelectableView+BoxLayout]:
    size_hint_y: ctx.size_hint_y
    height: ctx.height
    ListItemButton:
        text: ctx.text
''')


class AdaptersTestCase(unittest.TestCase):

    def setUp(self):
        self.args_converter = lambda row_index, rec: {'text': rec['name'],
                                                      'size_hint_y': None,
                                                      'height': 25}

        self.integers_dict = \
         {str(i): {'text': str(i), 'is_selected': False} for i in range(100)}

        # The third of the four cls_dict items has no kwargs nor text, so
        # rec['text'] will be set for it. Likewise, the fifth item has kwargs,
        # but it has no 'text' key/value, so should receive the same treatment.
        self.composite_args_converter = \
            lambda row_index, rec: \
                {'text': rec['text'],
                 'size_hint_y': None,
                 'height': 25,
                 'cls_dicts': [{'cls': ListItemButton,
                                'kwargs': {'text': rec['text']}},
                               {'cls': ListItemLabel,
                                'kwargs': {'text': "#-{0}".format(rec['text']),
                                           'is_representing_cls': True}},
                               {'cls': ListItemButton},
                               {'cls': ListItemButton,
                                'kwargs': {'some key': 'some value'}},
                               {'cls': ListItemButton,
                                'kwargs': {'text': rec['text']}}]}

        reset_to_defaults(fruit_data)

    @raises(Exception)
    def test_instantiating_an_adapter_with_neither_cls_nor_template(self):
        def dummy_converter():
            pass

        fruit_categories_list_adapter = \
            Adapter(data='cat',
                    args_converter=dummy_converter)

    def test_instantiating_an_adapter_with_neither_cls_nor_template(self):
        def dummy_converter():
            pass

        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(data='cat',
                        args_converter=dummy_converter)

        msg = 'adapter: a cls or template must be defined'
        self.assertEqual(str(cm.exception), msg)

        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(data='cat',
                        args_converter=dummy_converter,
                        cls=None)

        msg = 'adapter: a cls or template must be defined'
        self.assertEqual(str(cm.exception), msg)

        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(data='cat',
                        args_converter=dummy_converter,
                        template=None)

        msg = 'adapter: a cls or template must be defined'
        self.assertEqual(str(cm.exception), msg)

        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(data='cat',
                        args_converter=dummy_converter,
                        cls=None,
                        template=None)

        msg = 'adapter: cannot use cls and template at the same time'
        self.assertEqual(str(cm.exception), msg)

    def test_instantiating_an_adapter_with_no_data(self):
        # with no data
        with self.assertRaises(Exception) as cm:
            adapter = Adapter()

        msg = 'adapter: input must include data argument'
        self.assertEqual(str(cm.exception), msg)

    def test_instantiating_an_adapter_with_both_cls_and_template(self):
        from kivy.adapters.args_converters import list_item_args_converter

        with self.assertRaises(Exception) as cm:
            adapter = Adapter(data='cat',
                              args_converter=list_item_args_converter,
                              template='CustomListItem',
                              cls=ListItemButton)

        msg = 'adapter: cannot use cls and template at the same time'
        self.assertEqual(str(cm.exception), msg)

    def test_instantiating_adapter(self):
        from kivy.adapters.args_converters import list_item_args_converter

        def dummy_converter():
            pass

        class Adapter_1(Adapter):
            def __init__(self, **kwargs):
                kwargs['args_converter'] = dummy_converter
                super(Adapter_1, self).__init__(**kwargs)

        kwargs = {}
        kwargs['data'] = 'cat'
        kwargs['args_converter'] = dummy_converter
        kwargs['cls'] = ListItemButton

        my_adapter = Adapter(**kwargs)
        self.assertEqual(my_adapter.args_converter, dummy_converter)

        my_adapter = Adapter_1(**kwargs)
        self.assertEqual(my_adapter.args_converter, dummy_converter)

        kwargs_2 = {}
        kwargs_2['data'] = 'cat'
        kwargs_2['cls'] = ListItemButton

        adapter_2 = Adapter(**kwargs_2)
        self.assertEqual(adapter_2.args_converter, list_item_args_converter)

        adapter = Adapter(data='cat', cls=Label)
        self.assertEqual(adapter.get_data_item(), 'cat')

        adapter = Adapter(data=None, cls=Label)
        self.assertEqual(adapter.get_data_item(), None)

    def test_instantiating_adapter_bind_triggers_to_view(self):
        class PetListener(object):
            def __init__(self, pet):
                self.current_pet = pet

            def callback(self, *args):
                self.current_pet = args[1]

        pet_listener = PetListener('cat')

        adapter = Adapter(data='cat', cls=Label)
        adapter.bind_triggers_to_view(pet_listener.callback)

        self.assertEqual(pet_listener.current_pet, 'cat')
        adapter.data = 'dog'
        self.assertEqual(pet_listener.current_pet, 'dog')

    def test_simple_list_adapter_for_exceptions(self):
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

    def test_simple_list_adapter_with_template(self):
        list_item_args_converter = \
                lambda row_index, obj: {'text': str(obj),
                                        'size_hint_y': None,
                                        'height': 25}

        simple_list_adapter = \
                SimpleListAdapter(data=['cat', 'dog'],
                                  args_converter=list_item_args_converter,
                                  template='CustomSimpleListItem')

        view = simple_list_adapter.get_view(0)
        self.assertEqual(view.__class__.__name__, 'CustomSimpleListItem')

        # For coverage of __repr__:
        self.assertEqual(type(str(view)), str)

    def test_simple_list_adapter_methods(self):
        simple_list_adapter = SimpleListAdapter(data=['cat', 'dog'],
                                                cls=Label)
        self.assertEqual(simple_list_adapter.get_count(), 2)
        self.assertEqual(simple_list_adapter.get_data_item(0), 'cat')
        self.assertEqual(simple_list_adapter.get_data_item(1), 'dog')
        self.assertIsNone(simple_list_adapter.get_data_item(-1))
        self.assertIsNone(simple_list_adapter.get_data_item(2))

        view = simple_list_adapter.get_view(0)
        self.assertTrue(isinstance(view, Label))
        self.assertIsNone(simple_list_adapter.get_view(-1))
        self.assertIsNone(simple_list_adapter.get_view(2))

    def test_instantiating_list_adapter(self):
        str_args_converter = lambda row_index, rec: {'text': rec,
                                                     'size_hint_y': None,
                                                     'height': 25}

        list_adapter = ListAdapter(data=['cat', 'dog'],
                                         args_converter=str_args_converter,
                                         cls=ListItemButton)

        self.assertEqual([obj for obj in list_adapter.data],
                         ['cat', 'dog'])
        self.assertEqual(list_adapter.get_count(), 2)

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter, str_args_converter)
        self.assertEqual(list_adapter.template, None)

        cat_data_item = list_adapter.get_data_item(0)
        self.assertEqual(cat_data_item, 'cat')
        self.assertTrue(isinstance(cat_data_item, string_types))

        view = list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))

        view = list_adapter.create_view(0)
        self.assertTrue(isinstance(view, ListItemButton))

        view = list_adapter.create_view(-1)
        self.assertIsNone(view)

        view = list_adapter.create_view(100)
        self.assertIsNone(view)

    def test_list_adapter_selection_mode_single(self):
        fruit_data_items[0].is_selected = True

        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        list_adapter = ListAdapter(data=fruit_data_items,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   propagate_selection_to_data=True,
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual(sorted([obj.name for obj in list_adapter.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter,
                         list_item_args_converter)
        self.assertEqual(list_adapter.template, None)

        apple_data_item = list_adapter.get_data_item(0)
        self.assertTrue(isinstance(apple_data_item, FruitItem))
        self.assertTrue(isinstance(apple_data_item, SelectableDataItem))
        self.assertTrue(apple_data_item.is_selected)

        view = list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))
        self.assertTrue(view.is_selected)

    def test_list_adapter_with_dict_data(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        letters_dicts = \
           [{'text': l, 'is_selected': False} for l in alphabet]

        letters_dicts[0]['is_selected'] = True

        list_item_args_converter = lambda row_index, rec: {'text': rec['text'],
                                                           'size_hint_y': None,
                                                           'height': 25}

        list_adapter = ListAdapter(data=letters_dicts,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   propagate_selection_to_data=True,
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter,
                         list_item_args_converter)
        self.assertEqual(list_adapter.template, None)

        apple_data_item = list_adapter.get_data_item(0)
        self.assertTrue(isinstance(apple_data_item, dict))
        self.assertTrue(apple_data_item['is_selected'])

        view = list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))
        self.assertTrue(view.is_selected)

    def test_list_adapter_with_custom_data_item_class(self):

        class DataItem(object):
            def __init__(self, text='', is_selected=False):
                self.text = text
                self.is_selected = is_selected

        data_items = []
        data_items.append(DataItem(text='cat'))
        data_items.append(DataItem(text='dog'))
        data_items.append(DataItem(text='frog'))

        list_item_args_converter = lambda row_index, obj: {'text': obj.text,
                                                           'size_hint_y': None,
                                                           'height': 25}

        list_adapter = ListAdapter(data=data_items,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   propagate_selection_to_data=True,
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        data_item = list_adapter.get_data_item(0)
        self.assertTrue(isinstance(data_item, DataItem))
        self.assertTrue(data_item.is_selected)

        view = list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))
        self.assertTrue(view.is_selected)

    def test_list_adapter_with_widget_as_data_item_class(self):

        # Use a widget as data item.
        class DataItem(Label):
            is_selected = BooleanProperty(True)
            text = StringProperty('')

        class DataItemWithMethod(DataItem):
            _is_selected = BooleanProperty(True)

            def is_selected(self):
                return self._is_selected

        class BadDataItem(Label):
            text = StringProperty('')

        data_items = []
        data_items.append(DataItem(text='cat'))
        data_items.append(DataItemWithMethod(text='dog'))
        data_items.append(BadDataItem(text='frog'))

        list_item_args_converter = lambda row_index, obj: {'text': obj.text,
                                                           'size_hint_y': None,
                                                           'height': 25}

        list_adapter = ListAdapter(data=data_items,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   propagate_selection_to_data=True,
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter,
                         list_item_args_converter)
        self.assertEqual(list_adapter.template, None)

        data_item = list_adapter.get_data_item(0)
        self.assertTrue(isinstance(data_item, DataItem))
        self.assertTrue(data_item.is_selected)

        view = list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))
        self.assertTrue(view.is_selected)

        view = list_adapter.get_view(1)
        self.assertTrue(isinstance(view, ListItemButton))
        self.assertTrue(view.is_selected)

        with self.assertRaises(Exception) as cm:
            view = list_adapter.get_view(2)

        msg = "ListAdapter: unselectable data item for 2"
        self.assertEqual(str(cm.exception), msg)

    def test_instantiating_list_adapter_no_args_converter(self):
        list_adapter = \
                ListAdapter(data=['cat', 'dog'],
                            cls=ListItemButton)

        self.assertEqual(list_adapter.get_count(), 2)

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertIsNotNone(list_adapter.args_converter)
        self.assertEqual(list_adapter.template, None)

        cat_data_item = list_adapter.get_data_item(0)
        self.assertEqual(cat_data_item, 'cat')
        self.assertTrue(isinstance(cat_data_item, string_types))

        view = list_adapter.get_view(0)
        self.assertTrue(isinstance(view, ListItemButton))

        view = list_adapter.create_view(0)
        self.assertTrue(isinstance(view, ListItemButton))

        view = list_adapter.create_view(-1)
        self.assertIsNone(view)

        view = list_adapter.create_view(100)
        self.assertIsNone(view)

    def test_list_adapter_selection_mode_none(self):
        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        list_adapter = ListAdapter(data=fruit_data_items,
                                   args_converter=list_item_args_converter,
                                   selection_mode='none',
                                   allow_empty_selection=True,
                                   cls=ListItemButton)

        self.assertEqual(sorted([obj.name for obj in list_adapter.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter, list_item_args_converter)
        self.assertEqual(list_adapter.template, None)

        apple_data_item = list_adapter.get_data_item(0)
        self.assertTrue(isinstance(apple_data_item, FruitItem))

    def test_list_adapter_selection_mode_multiple_select_list(self):
        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        list_adapter = ListAdapter(data=fruit_data_items,
                                   args_converter=list_item_args_converter,
                                   selection_mode='multiple',
                                   allow_empty_selection=True,
                                   cls=ListItemButton)

        views = []
        views.append(list_adapter.get_view(0))
        views.append(list_adapter.get_view(1))
        views.append(list_adapter.get_view(2))

        self.assertEqual(len(views), 3)
        list_adapter.select_list(views)
        self.assertEqual(len(list_adapter.selection), 3)

        views = []
        views.append(list_adapter.get_view(3))
        views.append(list_adapter.get_view(4))
        views.append(list_adapter.get_view(5))

        self.assertEqual(len(views), 3)
        list_adapter.select_list(views)
        self.assertEqual(len(list_adapter.selection), 6)

        views = []
        views.append(list_adapter.get_view(0))
        views.append(list_adapter.get_view(1))
        views.append(list_adapter.get_view(2))

        self.assertEqual(len(views), 3)
        list_adapter.select_list(views, extend=False)
        self.assertEqual(len(list_adapter.selection), 3)

        list_adapter.deselect_list(views)
        self.assertEqual(len(list_adapter.selection), 0)

    def test_list_adapter_with_dicts_as_data(self):
        bare_minimum_dicts = \
            [{'text': str(i), 'is_selected': False} for i in range(100)]

        args_converter = lambda row_index, rec: {'text': rec['text'],
                                                 'size_hint_y': None,
                                                 'height': 25}

        list_adapter = ListAdapter(data=bare_minimum_dicts,
                                   args_converter=args_converter,
                                   selection_mode='none',
                                   allow_empty_selection=True,
                                   cls=ListItemButton)

        self.assertEqual([rec['text'] for rec in list_adapter.data],
            [str(i) for i in range(100)])

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter, args_converter)

        data_item = list_adapter.get_data_item(0)
        self.assertTrue(type(data_item), dict)

        # Utility calls for coverage:

        self.assertEqual(list_adapter.get_count(), 100)

        # Bad index:
        self.assertIsNone(list_adapter.get_data_item(-1))
        self.assertIsNone(list_adapter.get_data_item(101))

    def test_list_adapter_with_dicts_as_data_multiple_selection(self):
        bare_minimum_dicts = \
            [{'text': str(i), 'is_selected': False} for i in range(100)]

        args_converter = lambda row_index, rec: {'text': rec['text'],
                                                 'size_hint_y': None,
                                                 'height': 25}

        list_adapter = ListAdapter(data=bare_minimum_dicts,
                                   args_converter=args_converter,
                                   selection_mode='multiple',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual([rec['text'] for rec in list_adapter.data],
            [str(i) for i in range(100)])

        self.assertEqual(list_adapter.cls, ListItemButton)
        self.assertEqual(list_adapter.args_converter, args_converter)

        for i in range(50):
            list_adapter.handle_selection(list_adapter.get_view(i))

        self.assertEqual(len(list_adapter.selection), 50)

        # This is for code coverage:
        list_adapter.selection_mode = 'none'
        list_adapter.handle_selection(list_adapter.get_view(25))
        list_adapter.selection_mode = 'single'
        list_adapter.handle_selection(list_adapter.get_view(24))
        list_adapter.handle_selection(list_adapter.get_view(24))

    def test_list_adapter_bindings(self):
        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        fruit_categories_list_adapter = \
            ListAdapter(data=category_data_items,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        first_category_fruits = \
            fruit_categories[list(fruit_categories.keys())[0]]['fruits']

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

    def test_instantiating_list_adapters_with_both_cls_and_template(self):
        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['text'],
                                        'is_selected': rec['is_selected'],
                                        'size_hint_y': None,
                                        'height': 25}

        # First, for a plain Adapter:
        with self.assertRaises(Exception) as cm:
            fruit_categories_list_adapter = \
                Adapter(data='cat',
                        args_converter=list_item_args_converter,
                        template='CustomListItem',
                        cls=ListItemButton)

        msg = 'adapter: cannot use cls and template at the same time'
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

        msg = 'adapter: cannot use cls and template at the same time'
        self.assertEqual(str(cm.exception), msg)

    def test_view_from_list_adapter(self):

        # First with a class.
        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
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

        # Now with a template.
        list_item_args_converter = \
            lambda row_index, item: {'text': item.name,
                                     'is_selected': item.is_selected,
                                     'size_hint_y': None,
                                     'height': 25}

        fruit_categories_list_adapter = \
            ListAdapter(data=category_data_items,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        template='CustomListItem')

        view = fruit_categories_list_adapter.get_view(0)
        self.assertEqual(view.__class__.__name__, 'CustomListItem')

        second_view = fruit_categories_list_adapter.get_view(1)
        fruit_categories_list_adapter.handle_selection(second_view)
        self.assertEqual(len(fruit_categories_list_adapter.selection), 1)

    def test_list_adapter_operations_trimming(self):
        alphabet = [l for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']

        list_item_args_converter = \
                lambda row_index, letter: {'text': letter,
                                           'size_hint_y': None,
                                           'height': 25}

        # trim right of sel

        alphabet_adapter = ListAdapter(
                        data=alphabet,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        a_view = alphabet_adapter.get_view(0)
        self.assertEqual(a_view.text, 'A')

        alphabet_adapter.handle_selection(a_view)
        self.assertEqual(len(alphabet_adapter.selection), 1)
        self.assertTrue(a_view.is_selected)

        alphabet_adapter.trim_right_of_sel()
        self.assertEqual(len(alphabet_adapter.data), 1)

        # trim left of sel

        alphabet_adapter = ListAdapter(
                        data=alphabet,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        z_view = alphabet_adapter.get_view(25)
        self.assertEqual(z_view.text, 'Z')

        alphabet_adapter.handle_selection(z_view)
        self.assertEqual(len(alphabet_adapter.selection), 1)
        self.assertTrue(z_view.is_selected)

        alphabet_adapter.trim_left_of_sel()
        self.assertEqual(len(alphabet_adapter.data), 1)

        # trim to sel

        alphabet_adapter = ListAdapter(
                        data=alphabet,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        g_view = alphabet_adapter.get_view(6)
        self.assertEqual(g_view.text, 'G')
        alphabet_adapter.handle_selection(g_view)

        m_view = alphabet_adapter.get_view(12)
        self.assertEqual(m_view.text, 'M')
        alphabet_adapter.handle_selection(m_view)

        alphabet_adapter.trim_to_sel()
        self.assertEqual(len(alphabet_adapter.data), 7)

        # cut to sel

        alphabet_adapter = ListAdapter(
                        data=alphabet,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        g_view = alphabet_adapter.get_view(6)
        self.assertEqual(g_view.text, 'G')
        alphabet_adapter.handle_selection(g_view)

        m_view = alphabet_adapter.get_view(12)
        self.assertEqual(m_view.text, 'M')
        alphabet_adapter.handle_selection(m_view)

        alphabet_adapter.cut_to_sel()
        self.assertEqual(len(alphabet_adapter.data), 2)

    def test_list_adapter_reset_data(self):
        class PetListener(object):
            def __init__(self, pet):
                self.current_pet = pet

            # This should happen as a result of data changing.
            def callback(self, *args):
                self.current_pet = args[1]

        pet_listener = PetListener('cat')

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['text'],
                                        'size_hint_y': None,
                                        'height': 25}

        list_adapter = ListAdapter(
                        data=['cat'],
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        list_adapter.bind_triggers_to_view(pet_listener.callback)

        self.assertEqual(pet_listener.current_pet, 'cat')
        dog_data = ['dog']
        list_adapter.data = dog_data
        self.assertEqual(list_adapter.data, ['dog'])
        self.assertEqual(pet_listener.current_pet, dog_data)

        # Now just change an item.
        list_adapter.data[0] = 'cat'
        self.assertEqual(list_adapter.data, ['cat'])
        self.assertEqual(pet_listener.current_pet, ['cat'])

    def test_dict_adapter_composite(self):
        item_strings = ["{0}".format(index) for index in range(100)]

        # And now the list adapter, constructed with the item_strings as
        # the data, a dict to add the required is_selected boolean onto
        # data records, and the args_converter above that will operate one
        # each item in the data to produce list item view instances from the
        # CompositeListItem class.
        dict_adapter = DictAdapter(sorted_keys=item_strings,
                                   data=self.integers_dict,
                                   args_converter=self.composite_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)

        self.assertEqual(len(dict_adapter.selection), 1)

        view = dict_adapter.get_view(1)
        dict_adapter.handle_selection(view)

        self.assertEqual(len(dict_adapter.selection), 1)

    # test that sorted_keys is built, if not provided.
    def test_dict_adapter_no_sorted_keys(self):
        dict_adapter = DictAdapter(data=self.integers_dict,
                                   args_converter=self.composite_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)

        self.assertEqual(len(dict_adapter.sorted_keys), 100)

        self.assertEqual(len(dict_adapter.selection), 1)

        view = dict_adapter.get_view(1)
        dict_adapter.handle_selection(view)

        self.assertEqual(len(dict_adapter.selection), 1)

    def test_dict_adapter_bad_sorted_keys(self):
        with self.assertRaises(Exception) as cm:
            dict_adapter = DictAdapter(
                    sorted_keys={},
                    data=self.integers_dict,
                    args_converter=self.composite_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=CompositeListItem)

        msg = 'DictAdapter: sorted_keys must be tuple or list'
        self.assertEqual(str(cm.exception), msg)

    def test_instantiating_dict_adapter_bind_triggers_to_view(self):
        class PetListener(object):
            def __init__(self, pets):
                self.current_pets = pets

            def callback(self, *args):
                self.current_pets = args[1]

        pet_listener = PetListener(['cat'])

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['text'],
                                        'size_hint_y': None,
                                        'height': 25}

        dict_adapter = DictAdapter(sorted_keys=['cat'],
                data={'cat': {'text': 'cat', 'is_selected': False},
                      'dog': {'text': 'dog', 'is_selected': False}},
                args_converter=list_item_args_converter,
                propagate_selection_to_data=True,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)

        dict_adapter.bind_triggers_to_view(pet_listener.callback)

        self.assertEqual(pet_listener.current_pets, ['cat'])
        dict_adapter.sorted_keys = ['dog']
        self.assertEqual(pet_listener.current_pets, ['dog'])

    def test_dict_adapter_reset_data(self):
        class PetListener(object):
            def __init__(self, pet):
                self.current_pet = pet

            # This can happen as a result of sorted_keys changing,
            # or data changing.
            def callback(self, *args):
                self.current_pet = args[1]

        pet_listener = PetListener('cat')

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['text'],
                                        'size_hint_y': None,
                                        'height': 25}

        dict_adapter = DictAdapter(
                sorted_keys=['cat'],
                data={'cat': {'text': 'cat', 'is_selected': False}},
                args_converter=list_item_args_converter,
                propagate_selection_to_data=True,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)

        dict_adapter.bind_triggers_to_view(pet_listener.callback)

        self.assertEqual(pet_listener.current_pet, 'cat')
        dog_data = {'dog': {'text': 'dog', 'is_selected': False}}
        dict_adapter.data = dog_data
        self.assertEqual(dict_adapter.sorted_keys, ['dog'])
        self.assertEqual(pet_listener.current_pet, dog_data)
        cat_dog_data = {'cat': {'text': 'cat', 'is_selected': False},
                        'dog': {'text': 'dog', 'is_selected': False}}
        dict_adapter.data = cat_dog_data
        # sorted_keys should remain ['dog'], as it still matches data.
        self.assertEqual(dict_adapter.sorted_keys, ['dog'])
        dict_adapter.sorted_keys = ['cat']
        self.assertEqual(pet_listener.current_pet, ['cat'])

        # Make some utility calls for coverage:

        # 1, because get_count() does len(self.sorted_keys).
        self.assertEqual(dict_adapter.get_count(), 1)

        # Bad index:
        self.assertIsNone(dict_adapter.get_data_item(-1))
        self.assertIsNone(dict_adapter.get_data_item(2))

    def test_dict_adapter_selection_mode_single_without_propagation(self):

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['name'],
                                        'size_hint_y': None,
                                        'height': 25}

        dict_adapter = DictAdapter(sorted_keys=sorted(fruit_data.keys()),
                                   data=fruit_data,
                                   args_converter=list_item_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual(sorted(dict_adapter.data),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        self.assertEqual(dict_adapter.cls, ListItemButton)
        self.assertEqual(dict_adapter.args_converter, list_item_args_converter)
        self.assertEqual(dict_adapter.template, None)

        apple_data_item = dict_adapter.get_data_item(0)
        self.assertTrue(isinstance(apple_data_item, dict))
        self.assertEqual(apple_data_item['name'], 'Apple')

        apple_view = dict_adapter.get_view(0)
        self.assertTrue(isinstance(apple_view, ListItemButton))

        self.assertEqual(len(dict_adapter.selection), 1)
        self.assertTrue(apple_view.is_selected)
        self.assertFalse(apple_data_item['is_selected'])

    def test_dict_adapter_selection_mode_single_with_propagation(self):

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['name'],
                                        'size_hint_y': None,
                                        'height': 25}

        dict_adapter = DictAdapter(sorted_keys=sorted(fruit_data.keys()),
                                   data=fruit_data,
                                   args_converter=list_item_args_converter,
                                   propagate_selection_to_data=True,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual(sorted(dict_adapter.data),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        self.assertEqual(dict_adapter.cls, ListItemButton)
        self.assertEqual(dict_adapter.args_converter, list_item_args_converter)
        self.assertEqual(dict_adapter.template, None)

        apple_data_item = dict_adapter.get_data_item(0)
        self.assertTrue(isinstance(apple_data_item, dict))
        self.assertEqual(apple_data_item['name'], 'Apple')

        apple_view = dict_adapter.get_view(0)
        self.assertTrue(isinstance(apple_view, ListItemButton))

        self.assertEqual(len(dict_adapter.selection), 1)
        self.assertTrue(apple_view.is_selected)
        self.assertTrue(apple_data_item['is_selected'])

    def test_dict_adapter_sorted_keys(self):

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['name'],
                                        'size_hint_y': None,
                                        'height': 25}

        dict_adapter = DictAdapter(sorted_keys=sorted(fruit_data.keys()),
                                   data=fruit_data,
                                   args_converter=list_item_args_converter,
                                   propagate_selection_to_data=True,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        self.assertEqual(sorted(dict_adapter.data),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        apple_view = dict_adapter.get_view(0)
        self.assertEqual(apple_view.text, 'Apple')

        avocado_view = dict_adapter.get_view(1)
        self.assertEqual(avocado_view.text, 'Avocado')

        banana_view = dict_adapter.get_view(2)
        self.assertEqual(banana_view.text, 'Banana')

        dict_adapter.sorted_keys = ['Lemon', 'Pear', 'Tangerine']

        self.assertEqual(len(dict_adapter.sorted_keys), 3)

        self.assertEqual(sorted(dict_adapter.data),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        lemon_view = dict_adapter.get_view(0)
        self.assertEqual(lemon_view.text, 'Lemon')

        pear_view = dict_adapter.get_view(1)
        self.assertEqual(pear_view.text, 'Pear')

        tangerine_view = dict_adapter.get_view(2)
        self.assertEqual(tangerine_view.text, 'Tangerine')

    def test_dict_adapter_operations_trimming(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        letters_dict = \
           {l: {'text': l, 'is_selected': False} for l in alphabet}

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['text'],
                                        'size_hint_y': None,
                                        'height': 25}

        letters = [l for l in alphabet]

        def sorted_keys_ok(letters_dict_adapter):
            sorted_keys_ok = True
            for key in letters_dict_adapter.sorted_keys:
                if not key in letters_dict_adapter.data:
                    sorted_keys_ok = False
                    break
            return sorted_keys_ok

        # trim left of sel

        letters_dict_adapter = DictAdapter(
                        sorted_keys=letters[:],
                        data=letters_dict,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        a_view = letters_dict_adapter.get_view(0)
        self.assertEqual(a_view.text, 'A')

        letters_dict_adapter.handle_selection(a_view)
        self.assertEqual(len(letters_dict_adapter.selection), 1)
        self.assertTrue(a_view.is_selected)

        letters_dict_adapter.trim_right_of_sel()
        self.assertEqual(len(letters_dict_adapter.data), 1)

        self.assertTrue(sorted_keys_ok(letters_dict_adapter))

        # trim right of sel

        letters_dict_adapter = DictAdapter(
                        sorted_keys=letters[:],
                        data=letters_dict,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        z_view = letters_dict_adapter.get_view(25)
        self.assertEqual(z_view.text, 'Z')

        letters_dict_adapter.handle_selection(z_view)
        self.assertEqual(len(letters_dict_adapter.selection), 1)
        self.assertTrue(z_view.is_selected)

        letters_dict_adapter.trim_left_of_sel()
        self.assertEqual(len(letters_dict_adapter.data), 1)

        self.assertTrue(sorted_keys_ok(letters_dict_adapter))

        # trim to sel

        letters_dict_adapter = DictAdapter(
                        sorted_keys=letters[:],
                        data=letters_dict,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        g_view = letters_dict_adapter.get_view(6)
        self.assertEqual(g_view.text, 'G')
        letters_dict_adapter.handle_selection(g_view)

        m_view = letters_dict_adapter.get_view(12)
        self.assertEqual(m_view.text, 'M')
        letters_dict_adapter.handle_selection(m_view)

        letters_dict_adapter.trim_to_sel()
        self.assertEqual(len(letters_dict_adapter.data), 7)

        self.assertTrue(sorted_keys_ok(letters_dict_adapter))

        # cut to sel

        letters_dict_adapter = DictAdapter(
                        sorted_keys=letters[:],
                        data=letters_dict,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

        g_view = letters_dict_adapter.get_view(6)
        self.assertEqual(g_view.text, 'G')
        letters_dict_adapter.handle_selection(g_view)

        m_view = letters_dict_adapter.get_view(12)
        self.assertEqual(m_view.text, 'M')
        letters_dict_adapter.handle_selection(m_view)

        letters_dict_adapter.cut_to_sel()
        self.assertEqual(len(letters_dict_adapter.data), 2)

        self.assertTrue(sorted_keys_ok(letters_dict_adapter))

'''
Selection tests
===============

'''

import unittest

from kivy.binding import DataBinding
from kivy.binding import SelectionBinding

from kivy.controllers.listcontroller import ListController
from kivy.controllers.dictcontroller import DictController

from kivy.controllers.listcontroller import ListController

from kivy.event import EventDispatcher

from kivy.models import SelectableDataItem
from kivy.models import SelectableStringItem

from kivy.properties import OpObservableList
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import StringProperty

from kivy.selection import Selection
from kivy.selection import SelectionTool

from kivy.uix.widget import Widget
from kivy.uix.listview import ListView
from kivy.uix.listview import ListItemButton

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
                          'is_selected': False}}

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
                  'ksel': SelectionTool(False),
                  'Serving Size': fruit_record['Serving Size']},
            **dict(list(zip(list(attributes_and_units.keys()),
                            fruit_record['data']))))


class CategoryItem(SelectableDataItem):

    def __init__(self, **kwargs):
        super(CategoryItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.fruits = kwargs.get('fruits', [])

        self.ksel = SelectionTool(False)


class FruitItem(SelectableDataItem):

    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')
        self.data = kwargs.get('data', [])

        self.ksel = SelectionTool(False)


def reset_to_defaults(data):
    if type(data) is 'dict':
        for key in data:
            data[key]['ksel'].deselect()
    elif type(data) is 'list':
        for obj in data:
            obj.ksel.deselect()

category_data_items = \
    [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]

fruit_data_items = \
    [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]


class FruitSelectionObserver(Widget):
    fruit_name = StringProperty('')
    call_count = NumericProperty(0)

    def on_selection_change(self, list_controller, *args):
        if len(list_controller.selection) > 0:
            self.fruit_name = list_controller.selection[0].text
        self.call_count += 1


class FruitsDictController(DictController):

    def fruit_category_changed(self, fruit_categories_controller, *args):
        if len(fruit_categories_controller.selection) == 0:
            self.data = {}
            return

        category = \
                fruit_categories[str(fruit_categories_controller.selection[0])]
        self.sorted_keys = category['fruits']


class ListControllerTestCase(unittest.TestCase):

    def setUp(self):
        self.args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        reset_to_defaults(category_data_items)
        reset_to_defaults(fruit_data_items)
        reset_to_defaults(fruit_categories)
        reset_to_defaults(fruit_data)

    def test_list_controller_selection_mode_none(self):
        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='none',
                                   allow_empty_selection=True)

        self.assertEqual(sorted([obj.name for obj in list_controller.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        # The reason why len(selection) == 0 here is because it is ListView,
        # at the end of its __init__(), that calls check_for_empty_selection()
        # and triggers the initial selection, and we didn't make a ListView.
        self.assertEqual(len(list_controller.selection), 0)
        list_controller.check_for_empty_selection()
        self.assertEqual(len(list_controller.selection), 0)

    def test_list_controller_selection_mode_single(self):
        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='single',
                                   allow_empty_selection=True)
        list_view = ListView(data_binding=DataBinding(source=list_controller))

        # The reason why len(selection) == 0 here is because ListView,
        # at the end of its __init__(), calls check_for_empty_selection()
        # and does NOT trigger the initial selection, because we set
        # allow_empty_selection = True.
        self.assertEqual(len(list_controller.selection), 0)
        list_controller.check_for_empty_selection()

        # Nothing should have changed by that call, because still we have
        # allow_empty_selection = True, so no action in that check.
        self.assertEqual(len(list_controller.selection), 0)

        # Still no selection, but triggering a selection should make len = 1.
        # So, first we need to select the associated data item.
        self.assertEqual(fruit_data_items[0].name, 'Apple')
        fruit_data_items[0].ksel.select()
        apple = list_view.controller.get_view(0)
        self.assertEqual(apple.text, 'Apple')
        self.assertTrue(apple.ksel.is_selected())
        self.assertEqual(len(list_controller.selection), 1)

    def test_list_controller_selection_mode_single_auto_selection(self):
        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='single',
                                   allow_empty_selection=False)
        list_view = ListView(data_binding=DataBinding(source=list_controller))

        # The reason why len(selection) == 1 here is because ListView,
        # at the end of its __init__(), calls check_for_empty_selection()
        # and triggers the initial selection, because allow_empty_selection is
        # False.
        apple = list_view.controller.cached_views[0]
        self.assertEqual(list_controller.selection[0], apple)
        self.assertEqual(len(list_controller.selection), 1)
        list_controller.check_for_empty_selection()

        # Nothing should have changed for len, as we already have a selection.
        self.assertEqual(len(list_controller.selection), 1)

    def test_list_controller_selection_mode_multiple_auto_selection(self):
        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='multiple',
                                   allow_empty_selection=False)
        list_view = ListView(data_binding=DataBinding(source=list_controller))

        # The reason why len(selection) == 1 here is because ListView,
        # at the end of its __init__(), calls check_for_empty_selection()
        # and triggers the initial selection, because allow_empty_selection is
        # False.
        self.assertEqual(len(list_controller.selection), 1)
        apple = list_controller.selection[0]
        self.assertEqual(apple.text, 'Apple')

        # Add Avocado to the selection, doing necessary steps on data first.
        self.assertEqual(fruit_data_items[1].name, 'Avocado')
        fruit_data_items[1].ksel.select()
        avocado = list_view.controller.get_view(1)  # does selection
        self.assertEqual(avocado.text, 'Avocado')
        self.assertEqual(len(list_controller.selection), 2)

        # Re-selection of the same item should decrease the len by 1.
        list_controller.handle_selection(avocado)
        self.assertEqual(len(list_controller.selection), 1)
        # And now only apple should be in selection.
        self.assertEqual(list_controller.selection, [apple])

        # Selection of several different items should increment len,
        # because we have selection_mode as multiple.
        #
        # avocado has been unselected. Select it again.
        list_controller.handle_selection(avocado)
        self.assertEqual(len(list_controller.selection), 2)
        self.assertEqual(list_controller.selection, [apple, avocado])

        # And select some different ones.
        self.assertEqual(fruit_data_items[2].name, 'Banana')
        fruit_data_items[2].ksel.select()
        banana = list_view.controller.get_view(2)  # does selection
        self.assertEqual(list_controller.selection, [apple, avocado, banana])
        self.assertEqual(len(list_controller.selection), 3)

    def test_list_controller_selection_mode_multiple_and_limited(self):
        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='multiple',
                                   selection_limit=3,
                                   allow_empty_selection=True)
        list_view = ListView(data_binding=DataBinding(source=list_controller))

        # Selection should be limited to 3 items, because selection_limit = 3.
        for i in range(5):
            # Add item to the selection, doing necessary steps on data first.
            fruit_data_items[i].ksel.select()
            list_view.controller.get_view(i)  # does selection
            self.assertEqual(len(list_controller.selection),
                             i + 1 if i < 3 else 3)

    def test_list_controller_selection_handle_selection(self):
        list_controller = ListController(data=fruit_data_items,
                                   selection_mode='single',
                                   allow_empty_selection=False)

        selection_observer = FruitSelectionObserver()
        list_controller.bind(
                on_selection_change=selection_observer.on_selection_change)

        list_view = ListView(data_binding=DataBinding(source=list_controller))

        self.assertEqual(selection_observer.call_count, 0)

        # From the check for initial selection, we should have apple selected.
        self.assertEqual(list_controller.selection[0].text, 'Apple')
        self.assertEqual(len(list_controller.selection), 1)

        # Go through the tests routine to trigger selection of banana.
        # (See notes above about triggering selection in tests.)
        self.assertEqual(fruit_data_items[2].name, 'Banana')
        fruit_data_items[2].ksel.select()
        banana = list_view.controller.get_view(2)  # does selection
        self.assertEqual(banana.text, 'Banana')
        # Test with ksel.
        self.assertTrue(banana.ksel.is_selected())

        # Now unselect it with handle_selection().
        list_controller.handle_selection(banana)
        self.assertFalse(banana.ksel.is_selected())

        # But, since we have allow_empty_selection=False, Apple will be
        # reselected.
        self.assertEqual(selection_observer.fruit_name, 'Apple')

        # Call count:
        #
        # Apple got selected initally (0), then unselected when Banana was
        # selected (1). Then banana was unselected, causing reselection of
        # Apple (3). len should be 1.
        self.assertEqual(selection_observer.call_count, 3)
        self.assertEqual(len(list_controller.selection), 1)


class DictControllerTestCase(unittest.TestCase):

    def setUp(self):
        self.args_converter = lambda row_index, rec, key: {'text': rec['name'],
                                                           'size_hint_y': None,
                                                           'height': 25}

        self.fruits = sorted(fruit_data.keys())

        reset_to_defaults(fruit_categories)
        reset_to_defaults(fruit_data)

    def test_dict_controller_selection_cascade(self):

        # Categories of fruits:
        #
        categories = sorted(fruit_categories.keys())
        categories_dict_controller = \
            DictController(data=[SelectableStringItem(text=cat) for cat in categories],
                        data_dict=fruit_categories,
                        selection_mode='single',
                        allow_empty_selection=False)

        fruit_categories_list_view = \
            ListView(data_binding=DataBinding(source=categories_dict_controller),
                     size_hint=(.2, 1.0))

        # Fruits, for a given category, are shown based on the fruit category
        # selected in the first categories list above. The selected item in
        # the first list is used as the key into a dict of lists of list
        # items to reset the data in FruitsDictController's
        # fruit_category_changed() method.
        #
        # data is initially set to the first list of list items.
        #
        fruits_dict_controller = \
                FruitsDictController(
                    data=[SelectableStringItem(text=name) for name in fruit_categories[categories[0]]['fruits']],
                    data_dict=fruit_data,
                    selection_mode='single',
                    allow_empty_selection=False)

        categories_dict_controller.bind(
            on_selection_change=fruits_dict_controller.fruit_category_changed)

        fruits_list_view = ListView(data_binding=DataBinding(source=fruits_dict_controller),
                                    size_hint=(.2, 1.0))

        # List views should have controllers set.
        self.assertEqual(fruit_categories_list_view.data_binding.source,
                categories_dict_controller)
        self.assertEqual(fruits_list_view.data_binding.source, fruits_dict_controller)

        # Each list controller has allow_empty_selection=False, so each should
        # have one selected item.
        self.assertEqual(len(categories_dict_controller.selection), 1)
        self.assertEqual(len(fruits_dict_controller.selection), 1)

        # The selected list items should show selected.
        self.assertEqual(categories_dict_controller.selection[0].ksel.is_selected(),
                True)
        self.assertEqual(fruits_dict_controller.selection[0].ksel.is_selected(),
                True)


class ListControllerTestCase(unittest.TestCase):

    def setUp(self):
        reset_to_defaults(fruit_data_items)

    def test_list_controller_selection_mode_none(self):
        list_controller = ListController(data=fruit_data_items,
                                         selection_mode='none',
                                         allow_empty_selection=True)

        self.assertEqual(sorted([obj.name for obj in list_controller.data]),
            ['Apple', 'Avocado', 'Banana', 'Cantaloupe', 'Cherry', 'Grape',
             'Grapefruit', 'Honeydew', 'Kiwifruit', 'Lemon', 'Lime',
             'Nectarine', 'Orange', 'Peach', 'Pear', 'Pineapple', 'Plum',
             'Strawberry', 'Tangerine', 'Watermelon'])

        self.assertEqual(len(list_controller.selection), 0)
        list_controller.check_for_empty_selection(initialize_selection=True)
        self.assertEqual(len(list_controller.selection), 0)

        list_controller.allow_empty_selection = False
        list_controller.selection_mode = 'single'
        list_controller.check_for_empty_selection(initialize_selection=True)
        self.assertEqual(len(list_controller.selection), 1)

        list_controller.selection_mode = 'multiple'
        list_controller.select_list(list_controller.data)
        self.assertEqual(len(list_controller.selection),
                         len(list_controller.data))

    def test_list_controller_selection_external_changes(self):

        fruit_controller = ListController(data=[fruit_data_items[3],
                                                fruit_data_items[7],
                                                fruit_data_items[11],
                                                fruit_data_items[16]])

        list_controller = ListController(data=fruit_data_items,
                                         selection_binding=SelectionBinding(source=fruit_controller, prop='data'),
                                         selection_mode='multiple',
                                         allow_empty_selection=True)

        self.assertEqual(list_controller.selection,
                [fruit_data_items[3],
                 fruit_data_items[7],
                 fruit_data_items[11],
                 fruit_data_items[16]])

        three_sel = [fruit_data_items[2],
                     fruit_data_items[9],
                     fruit_data_items[13]]

        for sel in three_sel:
            sel.ksel.select()

        fruit_controller.data = three_sel
        self.assertEqual(list_controller.selection, three_sel)
        self.assertEqual(
            3, len([s for s in list_controller.selection if s.ksel.is_selected()]))

# TODO: The _value property of a binding is an ObjectProperty, to which
#       the OpObservableList property is bound, and receives the detailed op
#       dispatches, but as an ObjectProperty, this won't work. Maybe binding
#       needs a different scheme.
#
#        fruit_controller.data.insert(1, fruit_data_items[8])
#        four_sel = list(three_sel)
#        four_sel.insert(1, fruit_data_items[8])
#        self.assertEqual(list_controller.selection, four_sel)
#
#        ten_sel = fruit_data_items[:10]
#        fruit_controller.data = ten_sel
#        self.assertEqual(list_controller.selection, ten_sel)
#
#        nine_sel = list(ten_sel)
#        del nine_sel[5]
#        del list_controller.selection[5]
#        self.assertEqual(list_controller.selection, nine_sel)
#
#        list_controller.selection_limit = 5
#        list_controller.selection = ten_sel
#        self.assertEqual(5, len(list_controller.selection))

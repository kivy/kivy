'''
ListView tests
==============
'''

import unittest

from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.models import SelectableStringItem
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton, ListView


class ListViewTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple_list_view_explicit_simple_list_controller(self):

        simple_list_controller = \
            ListController(
                    data=[SelectableStringItem(text="Item #{0}".format(i)) for i in range(100)])

        list_view = ListView(data_binding=DataBinding(source=simple_list_controller),
                             list_item_class=ListItemButton)

        self.assertEqual(type(list_view.data_binding.source), ListController)
        self.assertTrue(hasattr(list_view.data_binding.source, 'selection'))
        self.assertEqual(len(list_view.data_binding.source.data), 100)

    def test_list_view_reset_data(self):
        class PetListener(object):
            def __init__(self, pet):
                self.current_pet = pet

            # This should happen as a result of data changing.
            def callback(self, *args):
                self.current_pet = args[1]

        pet_listener = PetListener('cat')

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec.text,
                                        'size_hint_y': None,
                                        'height': 25}

        list_controller = ListController(
                        data=[SelectableStringItem(text=s) for s in ['cat', 'dog', 'lizard', 'hamster', 'ferret']],
                        selection_mode='multiple',
                        allow_empty_selection=False)

        list_view = ListView(data_binding=DataBinding(source=list_controller),
                             list_item_class=ListItemButton)

        list_controller.bind(data=pet_listener.callback)

        self.assertEqual(pet_listener.current_pet, 'cat')

        pet_data = list_controller.data
        pet_data[2] = SelectableStringItem(text='bird')
        self.assertEqual([item.text for item in list_controller.data],
                         ['cat', 'dog', 'bird', 'hamster', 'ferret'])
        self.assertTrue(hasattr(list_view.data_binding.source, 'selection'))
        self.assertEqual(len(list_view.data_binding.source.data), 5)

    def test_list_view_with_list_of_integers(self):

        data = [SelectableStringItem(text=str(i)) for i in range(100)]

        args_converter = lambda row_index, rec: {'text': rec.text,
                                                 'size_hint_y': None,
                                                 'height': 25}

        list_controller = ListController(data=data,
                                         selection_mode='single',
                                         allow_empty_selection=False)

        list_view = ListView(data_binding=DataBinding(source=list_controller),
                             args_converter=args_converter,
                             list_item_class=ListItemButton)

        self.assertEqual(type(list_view.data_binding.source), ListController)
        self.assertTrue(hasattr(list_view.data_binding.source, 'selection'))
        self.assertEqual(len(list_view.data_binding.source.data), 100)

    def test_list_view_with_list_of_integers_scrolling(self):

        data = [SelectableStringItem(text=str(i)) for i in range(100)]

        args_converter = lambda row_index, rec: {'text': rec.text,
                                                 'size_hint_y': None,
                                                 'height': 25}

        list_controller = ListController(data=data,
                                         selection_mode='single',
                                         allow_empty_selection=False)

        list_view = ListView(data_binding=DataBinding(source=list_controller),
                             args_converter=args_converter,
                             list_item_class=ListItemButton)

        # TODO: This broke after the data_changed work to add more fine-grained
        #       data change dispatching to the controllers and to ListView. There
        #       was also work done on scrolling. Somehow, row_height setting is
        #       getting skipped now. So, in the meantime...  Manually set the
        #       row_height, which would be set when the ListView is
        #       instantiated in context.
        list_view.row_height = 20

        list_view.scroll_to(20)
        self.assertEqual(list_view._index, 20)

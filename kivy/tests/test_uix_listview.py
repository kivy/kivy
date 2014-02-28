'''
ListView tests
==============
'''

import unittest

from kivy.uix.label import Label
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.simplelistadapter import SimpleListAdapter
from kivy.uix.listview import ListItemButton, ListView


class ListViewTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple_list_view(self):

        list_view = \
                ListView(item_strings=[str(index) for index in range(100)])

        self.assertEqual(type(list_view.adapter), SimpleListAdapter)
        self.assertFalse(hasattr(list_view.adapter, 'selection'))
        self.assertEqual(len(list_view.adapter.data), 100)

    def test_simple_list_view_explicit_simple_list_adapter(self):

        simple_list_adapter = \
            SimpleListAdapter(
                    data=["Item #{0}".format(i) for i in range(100)],
                    cls=Label)

        list_view = ListView(adapter=simple_list_adapter)

        self.assertEqual(type(list_view.adapter), SimpleListAdapter)
        self.assertFalse(hasattr(list_view.adapter, 'selection'))
        self.assertEqual(len(list_view.adapter.data), 100)
        self.assertEqual(type(list_view.adapter.get_view(0)), Label)

    def test_list_view_reset_data(self):
        class PetListener(object):
            def __init__(self, pet):
                self.current_pet = pet

            # This should happen as a result of data changing.
            def callback(self, *args):
                self.current_pet = args[1]

        pet_listener = PetListener('cat')

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec,
                                        'size_hint_y': None,
                                        'height': 25}

        list_adapter = ListAdapter(
                        data=['cat', 'dog', 'lizard', 'hamster', 'ferret'],
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        list_view = ListView(adapter=list_adapter)

        list_adapter.bind_triggers_to_view(pet_listener.callback)

        self.assertEqual(pet_listener.current_pet, 'cat')
        self.assertEqual(list_view.adapter.get_view(2).text, 'lizard')

        pet_data = list_adapter.data
        pet_data[2] = 'bird'
        self.assertEqual(list_adapter.data, ['cat',
                                             'dog',
                                             'bird',
                                             'hamster',
                                             'ferret'])
        self.assertTrue(hasattr(list_view.adapter, 'selection'))
        self.assertEqual(len(list_view.adapter.data), 5)
        self.assertEqual(type(list_view.adapter.get_view(0)), ListItemButton)
        self.assertEqual(list_view.adapter.get_view(0).text, 'cat')
        self.assertEqual(list_view.adapter.get_view(2).text, 'bird')

    def test_list_view_with_list_of_integers(self):

        data = [{'text': str(i), 'is_selected': False} for i in range(100)]

        args_converter = lambda row_index, rec: {'text': rec['text'],
                                                 'size_hint_y': None,
                                                 'height': 25}

        list_adapter = ListAdapter(data=data,
                                   args_converter=args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        list_view = ListView(adapter=list_adapter)

        self.assertEqual(type(list_view.adapter), ListAdapter)
        self.assertTrue(hasattr(list_view.adapter, 'selection'))
        self.assertEqual(len(list_view.adapter.data), 100)
        self.assertEqual(type(list_view.adapter.get_view(0)), ListItemButton)

    def test_list_view_with_list_of_integers_scrolling(self):

        data = [{'text': str(i), 'is_selected': False} for i in range(100)]

        args_converter = lambda row_index, rec: {'text': rec['text'],
                                                 'size_hint_y': None,
                                                 'height': 25}

        list_adapter = ListAdapter(data=data,
                                   args_converter=args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=ListItemButton)

        list_view = ListView(adapter=list_adapter)

        list_view.scroll_to(20)
        self.assertEqual(list_view._index, 20)

    def test_simple_list_view_deletion(self):

        list_view = \
                ListView(item_strings=[str(index) for index in range(100)])

        self.assertEqual(len(list_view.adapter.data), 100)
        del list_view.adapter.data[49]
        self.assertEqual(len(list_view.adapter.data), 99)

    def test_list_view_declared_in_kv_with_item_strings(self):
        from kivy.lang import Builder
        from kivy.uix.modalview import ModalView
        from kivy.uix.widget import Widget
        from kivy.factory import Factory
        from kivy.properties import StringProperty, ObjectProperty, \
            BooleanProperty

        Builder.load_string("""
#:import label kivy.uix.label
#:import sla kivy.adapters.simplelistadapter

<ListViewModal>:
    size_hint: None,None
    size: 400,400
    lvm: lvm
    ListView:
        id: lvm
        size_hint: .8,.8
        item_strings: ["Item #{0}".format(i) for i in range(100)]
""")

        class ListViewModal(ModalView):
            def __init__(self, **kwargs):
                super(ListViewModal, self).__init__(**kwargs)

        list_view_modal = ListViewModal()

        list_view = list_view_modal.lvm

        self.assertEqual(len(list_view.adapter.data), 100)

    def test_list_view_declared_in_kv_with_adapter(self):
        from kivy.lang import Builder
        from kivy.uix.modalview import ModalView
        from kivy.uix.widget import Widget
        from kivy.factory import Factory
        from kivy.properties import StringProperty, ObjectProperty, \
            BooleanProperty

        Builder.load_string("""
#:import label kivy.uix.label
#:import sla kivy.adapters.simplelistadapter

<ListViewModal>:
    size_hint: None,None
    size: 400,400
    lvm: lvm
    ListView:
        id: lvm
        size_hint: .8,.8
        adapter:
            sla.SimpleListAdapter(
            data=["Item #{0}".format(i) for i in range(100)],
            cls=label.Label)
""")

        class ListViewModal(ModalView):
            def __init__(self, **kwargs):
                super(ListViewModal, self).__init__(**kwargs)

        list_view_modal = ListViewModal()

        list_view = list_view_modal.lvm

        self.assertEqual(len(list_view.adapter.data), 100)

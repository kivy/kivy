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
                ListView(item_strings=[str(index) for index in xrange(100)])

        self.assertEqual(type(list_view.adapter), SimpleListAdapter)
        self.assertFalse(hasattr(list_view.adapter, 'selection'))
        self.assertEqual(len(list_view.adapter.data), 100)

    def test_simple_list_view_explicit_simple_list_adapter(self):

        simple_list_adapter = \
            SimpleListAdapter(
                    data=["Item #{0}".format(i) for i in xrange(100)],
                    cls=Label)

        list_view = ListView(adapter=simple_list_adapter)

        self.assertEqual(type(list_view.adapter), SimpleListAdapter)
        self.assertFalse(hasattr(list_view.adapter, 'selection'))
        self.assertEqual(len(list_view.adapter.data), 100)
        self.assertEqual(type(list_view.adapter.get_view(0)), Label)

    def test_list_view_with_list_of_integers(self):

        data = [{'text': str(i), 'is_selected': False} for i in xrange(100)]

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

        data = [{'text': str(i), 'is_selected': False} for i in xrange(100)]

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
                ListView(item_strings=[str(index) for index in xrange(100)])

        self.assertEqual(len(list_view.adapter.data), 100)
        del list_view.adapter.data[49]
        self.assertEqual(len(list_view.adapter.data), 99)

    def test_list_view_bad_instantiation(self):
        with self.assertRaises(Exception) as cm:
            listview = ListView()

        msg = 'ListView: item_strings needed or an adapter'
        self.assertEqual(str(cm.exception), msg)

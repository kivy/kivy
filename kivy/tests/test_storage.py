'''
Storage tests
=============
'''

import unittest

class StorageTestCase(unittest.TestCase):
    def test_dict_storage(self):
        from kivy.storage.dictstore import DictStore
        data = {}
        self._do_store_test_empty(DictStore(data))
        self._do_store_test_filled(DictStore(data))

    def test_json_storage(self):
        from kivy.storage.jsonstore import JsonStore
        from tempfile import mkstemp
        from os import unlink, close

        try:
            tmpfd, tmpfn = mkstemp('.json')
            close(tmpfd)
            self._do_store_test_empty(JsonStore(tmpfn))
            self._do_store_test_filled(JsonStore(tmpfn))
        finally:
            unlink(tmpfn)

    def _do_store_test_empty(self, store):
        self.assertFalse(store.exists('plop'))
        self.assertRaises(KeyError, lambda: store.get('plop'))
        self.assertTrue(store.put('plop', 'hello world'))
        self.assertTrue(store.exists('plop'))
        self.assertTrue(store.get('plop') == 'hello world')

    def _do_store_test_filled(self, store):
        self.assertRaises(KeyError, lambda: store.get('plop2'))
        self.assertRaises(KeyError, lambda: store.delete('plop2'))
        self.assertTrue(store.exists('plop'))
        self.assertTrue(store.get('plop') == 'hello world')
        self.assertTrue(store.put('plop', 'hello world2'))
        self.assertTrue(store.get('plop') == 'hello world2')
        self.assertTrue(store.exists('plop'))
        self.assertTrue(store.delete('plop'))
        self.assertRaises(KeyError, lambda: store.delete('plop'))
        self.assertRaises(KeyError, lambda: store.get('plop'))

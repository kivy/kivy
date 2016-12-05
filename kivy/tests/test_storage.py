'''
Storage tests
=============
'''

import unittest
import os


class StorageTestCase(unittest.TestCase):
    def test_dict_storage(self):
        from kivy.storage.dictstore import DictStore
        from tempfile import mkstemp
        from os import unlink, close

        try:
            tmpfd, tmpfn = mkstemp('.dict')
            close(tmpfd)

            self._do_store_test_empty(DictStore(tmpfn))
            self._do_store_test_filled(DictStore(tmpfn))
        finally:
            unlink(tmpfn)

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

        try:
            tmpfd, tmpfn = mkstemp('.json')
            close(tmpfd)
            self._do_store_test_empty(JsonStore(tmpfn, indent=2))
            self._do_store_test_filled(JsonStore(tmpfn, indent=2))
        finally:
            unlink(tmpfn)

        try:
            tmpfd, tmpfn = mkstemp('.json')
            close(tmpfd)
            self._do_store_test_empty(JsonStore(tmpfn, sort_keys=True))
            self._do_store_test_filled(JsonStore(tmpfn, sort_keys=True))
        finally:
            unlink(tmpfn)

    def test_redis_storage(self):
        if os.environ.get('NONETWORK'):
            return
        try:
            from kivy.storage.redisstore import RedisStore
            from redis.exceptions import ConnectionError
            try:
                params = dict(db=15)
                self._do_store_test_empty(RedisStore(params))
                self._do_store_test_filled(RedisStore(params))
            except ConnectionError:
                pass
        except ImportError:
            pass

    def _do_store_test_empty(self, store):
        store.clear()
        self.assertTrue(store.count() == 0)
        self.assertFalse(store.exists('plop'))
        self.assertRaises(KeyError, lambda: store.get('plop'))
        self.assertTrue(store.put('plop', name='Hello', age=30))
        self.assertTrue(store.exists('plop'))
        self.assertTrue(store.get('plop').get('name') == 'Hello')
        self.assertTrue(store.get('plop').get('age') == 30)
        self.assertTrue(store.count() == 1)
        self.assertTrue('plop' in store.keys())

        # test queries
        store.put('key1', name='Name1', attr1='Common')
        store.put('key2', name='Name2', attr1='Common', attr2='bleh')
        store.put('key3', name='Name3', attr1='Common', attr2='bleh')
        self.assertTrue(store.count() == 4)
        self.assertTrue(store.exists('key1'))
        self.assertTrue(store.exists('key2'))
        self.assertTrue(store.exists('key3'))

        self.assertTrue(len(list(store.find(name='Name2'))) == 1)
        self.assertTrue(list(store.find(name='Name2'))[0][0] == 'key2')
        self.assertTrue(len(list(store.find(attr1='Common'))) == 3)
        self.assertTrue(len(list(store.find(attr2='bleh'))) == 2)
        self.assertTrue(
            len(list(store.find(attr1='Common', attr2='bleh'))) == 2)
        self.assertTrue(len(list(store.find(name='Name2', attr2='bleh'))) == 1)
        self.assertTrue(len(list(store.find(name='Name1', attr2='bleh'))) == 0)

    def _do_store_test_filled(self, store):
        self.assertTrue(store.count() == 4)
        self.assertRaises(KeyError, lambda: store.get('plop2'))
        self.assertRaises(KeyError, lambda: store.delete('plop2'))
        self.assertTrue(store.exists('plop'))
        self.assertTrue(store.get('plop').get('name') == 'Hello')
        self.assertTrue(store.put('plop', name='World', age=1))
        self.assertTrue(store.get('plop').get('name') == 'World')
        self.assertTrue(store.exists('plop'))
        self.assertTrue(store.delete('plop'))
        self.assertRaises(KeyError, lambda: store.delete('plop'))
        self.assertRaises(KeyError, lambda: store.get('plop'))

'''
Storage tests
=============
'''

import unittest
from os.path import abspath, dirname, join
import errno
import os
from tempfile import TemporaryDirectory
from unittest.mock import patch
from stat import S_IMODE


class StorageTestCase(unittest.TestCase):
    def test_json_storage_respects_read_only_file(self):
        import stat
        from kivy.storage.jsonstore import JsonStore

        with TemporaryDirectory() as folder:
            filename = join(folder, 'store.json')
            store = JsonStore(filename)
            store.put('saved', value='original')
            mode = stat.S_IMODE(os.stat(filename).st_mode)
            os.chmod(filename, stat.S_IRUSR)
            try:
                # Root or an unusual filesystem may ignore the mode bits.
                try:
                    fd = os.open(filename, os.O_WRONLY)
                except PermissionError:
                    pass
                else:
                    os.close(fd)
                    self.skipTest('filesystem permits writing read-only files')
                with self.assertRaises(PermissionError):
                    store.put('saved', value='replacement')
                self.assertEqual(JsonStore(filename).get('saved'),
                                 {'value': 'original'})
                self.assertTrue(store._is_changed)
                self.assertEqual(os.listdir(folder), ['store.json'])
            finally:
                os.chmod(filename, mode)

    def test_json_storage_does_not_remove_existing_temporary_file(self):
        from kivy.storage.jsonstore import JsonStore
        from uuid import UUID

        with TemporaryDirectory() as folder:
            filename = join(folder, 'store.json')
            store = JsonStore(filename)
            store.put('saved', value='original')
            identifier = UUID(int=0)
            temporary = join(folder, '.kivy-json-' + identifier.hex)
            with open(temporary, 'w') as fd:
                fd.write('unrelated data')
            with patch('kivy.storage.jsonstore.uuid4',
                       return_value=identifier):
                with self.assertRaises(FileExistsError):
                    store.put('saved', value='replacement')
            with open(temporary) as fd:
                self.assertEqual(fd.read(), 'unrelated data')
            self.assertEqual(JsonStore(filename).get('saved'),
                             {'value': 'original'})

    def test_json_storage_failed_write_does_not_create_file(self):
        from kivy.storage.jsonstore import JsonStore

        with TemporaryDirectory() as folder:
            store = JsonStore(join(folder, 'store.json'))
            with self.assertRaises(TypeError):
                store.put('invalid', value=object())
            self.assertTrue(store._is_changed)
            self.assertEqual(os.listdir(folder), [])

    def test_json_storage_replace_failure_can_retry(self):
        from kivy.storage.jsonstore import JsonStore

        with TemporaryDirectory() as folder:
            filename = join(folder, 'store.json')
            store = JsonStore(filename)
            store.put('saved', value='original')
            with patch('kivy.storage.jsonstore.replace',
                       side_effect=OSError('replace failed')):
                with self.assertRaisesRegex(OSError, 'replace failed'):
                    store.put('saved', value='replacement')
            self.assertEqual(JsonStore(filename).get('saved'),
                             {'value': 'original'})
            self.assertEqual(os.listdir(folder), ['store.json'])
            self.assertTrue(store._is_changed)
            store.store_sync()
            self.assertFalse(store._is_changed)
            self.assertEqual(JsonStore(filename).get('saved'),
                             {'value': 'replacement'})

    def test_json_storage_preserves_file_permissions(self):
        from kivy.storage.jsonstore import JsonStore

        with TemporaryDirectory() as folder:
            control = join(folder, 'control.json')
            with open(control, 'w') as fd:
                fd.write('{}')
            filename = join(folder, 'store.json')
            store = JsonStore(filename)
            store.put('saved', value='original')
            self.assertEqual(S_IMODE(os.stat(filename).st_mode),
                             S_IMODE(os.stat(control).st_mode))
            os.chmod(filename, 0o640)
            mode = S_IMODE(os.stat(filename).st_mode)
            store.put('saved', value='replacement')
            self.assertEqual(S_IMODE(os.stat(filename).st_mode), mode)

    def test_json_storage_preserves_symlink(self):
        from kivy.storage.jsonstore import JsonStore

        with TemporaryDirectory() as folder:
            target = join(folder, 'target.json')
            JsonStore(target).put('saved', value='original')
            filename = join(folder, 'store.json')
            try:
                os.symlink('target.json', filename)
            except (OSError, NotImplementedError):
                self.skipTest('Symbolic links are unavailable')
            JsonStore(filename).put('saved', value='replacement')
            self.assertTrue(os.path.islink(filename))
            self.assertEqual(os.readlink(filename), 'target.json')
            self.assertEqual(JsonStore(target).get('saved'),
                             {'value': 'replacement'})
            self.assertEqual(sorted(os.listdir(folder)),
                             ['store.json', 'target.json'])

    def test_json_storage_interrupted_write_preserves_existing_file(self):
        from kivy.storage.jsonstore import JsonStore

        def interrupted_dump(data, fd, **kwargs):
            fd.write('{"incomplete":')
            fd.flush()
            raise OSError('interrupted write')

        with TemporaryDirectory() as folder:
            filename = join(folder, 'store.json')
            store = JsonStore(filename)
            store.put('saved', value='original')
            with open(filename, 'rb') as fd:
                original = fd.read()

            with patch('kivy.storage.jsonstore.dump', interrupted_dump):
                with self.assertRaisesRegex(OSError, 'interrupted write'):
                    store.put('saved', value='replacement')

            with open(filename, 'rb') as fd:
                self.assertEqual(fd.read(), original)
            self.assertEqual(JsonStore(filename).get('saved'),
                             {'value': 'original'})
            self.assertTrue(store._is_changed)
            self.assertEqual(os.listdir(folder), ['store.json'])
            store.store_sync()
            self.assertEqual(JsonStore(filename).get('saved'),
                             {'value': 'replacement'})

    def test_json_storage_failed_write_preserves_existing_file(self):
        from kivy.storage.jsonstore import JsonStore

        with TemporaryDirectory() as folder:
            filename = join(folder, 'store.json')
            store = JsonStore(filename)
            store.put('saved', value='original')
            with open(filename, 'rb') as fd:
                original = fd.read()

            with self.assertRaises(TypeError):
                store.put('invalid', value=object())

            with open(filename, 'rb') as fd:
                self.assertEqual(fd.read(), original)
            self.assertEqual(JsonStore(filename).get('saved'),
                             {'value': 'original'})
            self.assertTrue(store._is_changed)
            self.assertEqual(os.listdir(folder), ['store.json'])

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

    def test_dict_storage_nofolder(self):
        from kivy.storage.dictstore import DictStore
        self._do_store_test_nofolder(DictStore)

    def test_json_storage_nofolder(self):
        from kivy.storage.jsonstore import JsonStore
        self._do_store_test_nofolder(JsonStore)

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

    def _do_store_test_nofolder(self, store_cls):
        ext = store_cls.__name__.lower()[:4]
        path = join(
            dirname(abspath(__file__)),
            '__i_dont_exist__',
            'test.' + ext
        )
        with self.assertRaises(IOError) as context:
            store = store_cls(path)
        self.assertEqual(context.exception.errno, errno.ENOENT)


if __name__ == '__main__':
    unittest.main()

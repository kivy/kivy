'''
Dictionary store
=================

Use a Python dictionary as a store.
'''

__all__ = ('DictStore', )

try:
    import cPickle as pickle
except ImportError:
    import pickle

from os.path import exists
from kivy.compat import iteritems
from kivy.storage import AbstractStore


class DictStore(AbstractStore):
    '''Store implementation using a pickled `dict`.
    See the :mod:`kivy.storage` module documentation for more information.
    '''
    def __init__(self, filename, data=None, **kwargs):
        if isinstance(filename, dict):
            # backward compatibility, first argument was a dict.
            self.filename = None
            self._data = filename
        else:
            self.filename = filename
            self._data = data or {}
        self._is_changed = True
        super(DictStore, self).__init__(**kwargs)

    def store_load(self):
        if self.filename is None:
            return
        if not exists(self.filename):
            return
        with open(self.filename, 'rb') as fd:
            data = fd.read()
            if data:
                self._data = pickle.loads(data)

    def store_sync(self):
        if self.filename is None:
            return
        if not self._is_changed:
            return

        with open(self.filename, 'wb') as fd:
            pickle.dump(self._data, fd)

        self._is_changed = False

    def store_exists(self, key):
        return key in self._data

    def store_get(self, key):
        return self._data[key]

    def store_put(self, key, value):
        self._data[key] = value
        self._is_changed = True
        return True

    def store_delete(self, key):
        del self._data[key]
        self._is_changed = True
        return True

    def store_find(self, filters):
        for key, values in iteritems(self._data):
            found = True
            for fkey, fvalue in iteritems(filters):
                if fkey not in values:
                    found = False
                    break
                if values[fkey] != fvalue:
                    found = False
                    break
            if found:
                yield key, values

    def store_count(self):
        return len(self._data)

    def store_keys(self):
        return list(self._data.keys())

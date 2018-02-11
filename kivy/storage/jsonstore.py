'''
JSON store
==========

A :mod:`Storage <kivy.storage>` module used to save/load key-value pairs from
a json file.
'''

__all__ = ('JsonStore', )


import errno
from os.path import exists, abspath, dirname
from kivy.compat import iteritems
from kivy.storage import AbstractStore
from json import loads, dump


class JsonStore(AbstractStore):
    '''Store implementation using a json file for storing the key-value pairs.
    See the :mod:`kivy.storage` module documentation for more information.
    '''
    def __init__(self, filename, indent=None, sort_keys=False, **kwargs):
        self.filename = filename
        self.indent = indent
        self.sort_keys = sort_keys
        self._data = {}
        self._is_changed = True
        super(JsonStore, self).__init__(**kwargs)

    def store_load(self):
        if not exists(self.filename):
            folder = abspath(dirname(self.filename))
            if not exists(folder):
                not_found = IOError(
                    "The folder '{}' doesn't exist!"
                    "".format(folder)
                )
                not_found.errno = errno.ENOENT
                raise not_found
            return
        with open(self.filename) as fd:
            data = fd.read()
            if len(data) == 0:
                return
            self._data = loads(data)

    def store_sync(self):
        if not self._is_changed:
            return
        with open(self.filename, 'w') as fd:
            dump(
                self._data, fd,
                indent=self.indent,
                sort_keys=self.sort_keys
            )
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
        return self._data.keys()

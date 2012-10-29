'''
JSON store
==========

Can be used to save/load key/value from a json file.
'''

__all__ = ('JsonStore', )


from os.path import exists
from kivy.storage import AbstractStore
from json import loads, dump


class JsonStore(AbstractStore):
    '''Store implementation using a json file for storing the keys/values.
    See module documentation for more informations.
    '''
    def __init__(self, filename, **kwargs):
        self.filename = filename
        self._data = {}
        self._is_changed = True
        super(JsonStore, self).__init__(**kwargs)

    def store_load(self):
        if not exists(self.filename):
            return
        with open(self.filename) as fd:
            data = fd.read()
            if len(data) == 0:
                return
            self._data = loads(data)

    def store_sync(self):
        print 'SAAAAAAAVE', self.filename
        if self._is_changed is False:
            return
        with open(self.filename, 'w') as fd:
            dump(self._data, fd)
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


'''
Dictionnary store
=================

Use a Python dictionnary as a store.
'''

__all__ = ('DictStore', )


from kivy.compat import iteritems
from kivy.storage import AbstractStore


class DictStore(AbstractStore):
    '''Store implementation using a simple `dict`.
    '''
    def __init__(self, data=None, **kwargs):
        super(DictStore, self).__init__(**kwargs)
        if data is None:
            data = {}
        self.data = data

    def store_exists(self, key):
        return key in self.data

    def store_get(self, key):
        return self.data[key]

    def store_put(self, key, value):
        self.data[key] = value
        return True

    def store_delete(self, key):
        del self.data[key]
        return True

    def store_find(self, filters):
        for key, values in iteritems(self.data):
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
        return len(self.data)

    def store_keys(self):
        return self.data.keys()

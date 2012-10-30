'''
Dictionnary store
=================

Use a Python dictionnary as a store.
'''

__all__ = ('DictStore', )


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
        for key, values in self.data.iteritems():
            found = True
            for fkey, fvalue in filters.iteritems():
                if fkey not in values:
                    found = False
                    break
                if values[fkey] != fvalue:
                    found = False
                    break
            if found:
                yield key, values

'''
Storage
=======

.. versionadded:: 1.5.0

.. warning::

    This module is still experimental, and his API is subject to change in a
    future version.

Usage
-----

The idea behind the Storage module is to be able to load/store keys/values. The
default model is abstract, and you cannot use it directly. We provide some
implementation like:

- :class:`kivy.storage.jsonstore.DictStore`: use a python dict as a storage
- :class:`kivy.storage.jsonstore.JsonStore`: use a JSON file as a storage


Examples
--------

For example, let's use a JsonStore::

    from kivy.storage.jsonstore import JsonStore

    store = JsonStore('hello.json')

    # put some values
    store.put('tito', name='Mathieu', age=30)
    store.put('tshirtman', name='Gabriel', age=27)

    # get from a key
    print 'tito is', store.get('tito')

    # or guess the key/entry for a part of the key
    key, tshirtman = store.find(name='Gabriel')
    print 'tshirtman is', tshirtman

Because the data is persistant, i can check later if the key exists::

    from kivy.storage.jsonstore import JsonStore

    store = JsonStore('hello.json')
    if store.exists('tite'):
        print 'tite exists:', store.get('tito')
        store.delete('tito')


Synchronous / Asynchronous API
------------------------------

All the standard method (:meth:`~AbstractStore.get`, :meth:`~AbstractStore.put`,
:meth:`~AbstractStore.exists`, :meth:`~AbstractStore.delete`,
:meth:`~AbstractStore.find`) got an asynchronous version of it.

For example


have a `callback` parameter. If set, the callback will be used
to return the result to the user when available: the request will be
asynchronous.  If the `callback` is None, then the request will be synchronous
and the result will be returned directly.


Without callback (Synchronous API)::

    entry = mystore.get('tito')
    print 'tito =', entry

With callback (Asynchronous API):

    def my_callback(store, key, entry):
        print 'the key', key, 'have', entry
    mystore.get('plop', callback=my_callback)


The callback signature is `callback(store, key, result)`:

#. `store` is the `Store` instance currently used
#. `key` is the key searched
#. `entry` is the result of the lookup for the `key`




'''

from kivy.clock import Clock
from kivy.event import EventDispatcher
from functools import partial


class AbstractStore(EventDispatcher):
    '''Abstract class used to implement a Store
    '''

    def __init__(self, **kwargs):
        super(AbstractStore, self).__init__(**kwargs)
        self.store_load()

    def exists(self, key, callback=None):
        '''Check if a key exist in the storage.
        '''
        if callback is None:
            return self.store_exists(key)
        self._schedule(self.store_exists_async,
                key=key, callback=callback)

    def get(self, key):
        '''Get the value stored at `key`. If the key is not found, an
        `KeyError` exception will be throw.
        '''
        return self.store_get(key)

    def async_get(self, callback, key):
        '''Asynchronously get the value stored at `key`. The result will be sent
        through the `callback`.
        '''
        self._schedule(self.store_get_async, key=key, callback=callback)

    def put(self, key, **values):
        '''Put a new key/value in the storage
        '''
        need_sync = self.store_put(key, values)
        if need_sync:
            self.store_sync()
        return need_sync

    def async_put(self, callback, key, **values):
        '''Asynchronously put values in the `key` identifier.
        '''
        self._schedule(self.store_put_async,
                key=key, value=values, callback=callback)

    def delete(self, key):
        '''Delete a key from the storage. If the key is not found, an `KeyError`
        exception will be throw.  '''
        need_sync = self.store_delete(key)
        if need_sync:
            self.store_sync()
        return need_sync

    def async_delete(self, callback, key):
        '''Asynchronously delete the `key`.
        '''
        self._schedule(self.store_delete_async, key=key,
                callback=callback)

    def find(self, **filters):
        '''Return all the entries matching the filters. The entries are given
        through a generator, as a list of (key, entry)::

            for key, entry in store.find(name='Mathieu'):
                print 'entry:', key, '->', value

        Because it's a generator, you cannot directly use it as a list. You can do::

            # get all the (key, entry) availables
            entries = list(store.find(name='Mathieu'))
            # get only the entry from (key, entry)
            entries = list((x[1] for x in store.find(name='Mathieu')))
        '''
        return self.store_find(filters)

    def async_find(self, callback, **filters):
        '''Asynchronously return all the entries matching the filters. The
        callback will be called for every result found. When all the result have
        been returned, the callback will be called with 'None' as `key` and
        `entry`.
        '''
        self._schedule(self.store_find_async,
                callback=callback, filters=filters)

    #
    # Used for implementation
    #

    def store_get(self, key):
        raise NotImplemented()

    def store_put(self, key, value):
        raise NotImplemented()

    def store_exists(self, key):
        raise NotImplemented()

    def store_delete(self, key):
        raise NotImplemented()

    def store_load(self):
        pass

    def store_find(self, filters):
        return []

    def store_sync(self):
        pass

    def store_get_async(self, key, callback):
        try:
            value = self.store_get(key)
            callback(self, key, value)
        except KeyError:
            callback(self, key, None)

    def store_put_async(self, key, value, callback):
        try:
            value = self.store_put(key, value)
            callback(self, key, value)
        except:
            callback(self, key, None)

    def store_exists_async(self, key, callback):
        try:
            value = self.store_exists(key)
            callback(self, key, value)
        except:
            callback(self, key, None)

    def store_delete_async(self, key, callback):
        try:
            value = self.store_delete(key)
            callback(self, key, value)
        except:
            callback(self, key, None)

    def store_find_async(self, filters, callback):
        for key, entry in self.store_find(filters):
            callback(self, filters, key, entry)
        callback(self, filters, None, None)

    #
    # Privates
    #

    def _schedule(self, callback, **kwargs):
        # XXX not entirely sure about the best value (0 or -1).
        Clock.schedule_once(partial(callback, **kwargs), 0)

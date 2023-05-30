'''
Storage
=======

.. versionadded:: 1.7.0

.. warning::

    This module is still experimental, and the API is subject to change in a
    future version.

Usage
-----

The idea behind the Storage module is to be able to load/store any number of
key-value pairs via an indexed key. The default model is abstract so you
cannot use it directly. We provide some implementations such as:

- :class:`kivy.storage.dictstore.DictStore`: use a python dict as a store
- :class:`kivy.storage.jsonstore.JsonStore`: use a
  `JSON <https://en.wikipedia.org/wiki/JSON>`_ file as a store
- :class:`kivy.storage.redisstore.RedisStore`: use a `Redis <http://redis.io>`_
  database with `redis-py <https://github.com/andymccurdy/redis-py>`_


Examples
--------

For example, let's use a JsonStore::

    from kivy.storage.jsonstore import JsonStore

    store = JsonStore('hello.json')

    # put some values
    store.put('tito', name='Mathieu', org='kivy')
    store.put('tshirtman', name='Gabriel', age=27)

    # using the same index key erases all previously added key-value pairs
    store.put('tito', name='Mathieu', age=30)

    # get a value using a index key and key
    print('tito is', store.get('tito')['age'])

    # or guess the key/entry for a part of the key
    for item in store.find(name='Gabriel'):
        print('tshirtmans index key is', item[0])
        print('his key value pairs are', str(item[1]))

Because the data is persistent, you can check later to see if the key exists::

    from kivy.storage.jsonstore import JsonStore

    store = JsonStore('hello.json')
    if store.exists('tito'):
        print('tite exists:', store.get('tito'))
        store.delete('tito')


Synchronous / Asynchronous API
------------------------------

All the standard methods (:meth:`~AbstractStore.get`,
:meth:`~AbstractStore.put` , :meth:`~AbstractStore.exists`,
:meth:`~AbstractStore.delete`, :meth:`~AbstractStore.find`) have an
asynchronous version.

For example, the *get* method has a `callback` parameter. If set, the
`callback` will be used to return the result to the user when available:
the request will be asynchronous. If the `callback` is None, then the
request will be synchronous and the result will be returned directly.


Without callback (Synchronous API)::

    entry = mystore.get('tito')
    print('tito =', entry)

With callback (Asynchronous API)::

    def my_callback(store, key, result):
        print('the key', key, 'has a value of', result)
    mystore.get('plop', callback=my_callback)


The callback signature (for almost all methods) is::

    def callback(store, key, result):
        """
        store: the `Store` instance currently used.
        key: the key sought for.
        result: the result of the lookup for the key.
        """


Synchronous container type
--------------------------

The storage API emulates the container type for the synchronous API::

    store = JsonStore('hello.json')

    # original: store.get('tito')
    store['tito']

    # original: store.put('tito', name='Mathieu')
    store['tito'] = {'name': 'Mathieu'}

    # original: store.delete('tito')
    del store['tito']

    # original: store.count()
    len(store)

    # original: store.exists('tito')
    'tito' in store

    # original: for key in store.keys()
    for key in store:
        pass

'''

from kivy.clock import Clock
from kivy.event import EventDispatcher


class AbstractStore(EventDispatcher):
    '''Abstract class used to implement a Store
    '''

    def __init__(self, **kwargs):
        super(AbstractStore, self).__init__(**kwargs)
        self.store_load()

    def exists(self, key):
        '''Check if a key exists in the store.
        '''
        return self.store_exists(key)

    def async_exists(self, callback, key):
        '''Asynchronous version of :meth:`exists`.

        :Callback arguments:
            `store`: :class:`AbstractStore` instance
                Store instance
            `key`: string
                Name of the key to search for
            `result`: boo
                Result of the query, None if any error
        '''
        self._schedule(self.store_exists_async,
                       key=key, callback=callback)

    def get(self, key):
        '''Get the key-value pairs stored at `key`. If the key is not found, a
        `KeyError` exception will be thrown.
        '''
        return self.store_get(key)

    def async_get(self, callback, key):
        '''Asynchronous version of :meth:`get`.

        :Callback arguments:
            `store`: :class:`AbstractStore` instance
                Store instance
            `key`: string
                Name of the key to search for
            `result`: dict
                Result of the query, None if any error
        '''
        self._schedule(self.store_get_async, key=key, callback=callback)

    def put(self, key, **values):
        '''Put new key-value pairs (given in *values*) into the storage. Any
        existing key-value pairs will be removed.
        '''
        need_sync = self.store_put(key, values)
        if need_sync:
            self.store_sync()
        return need_sync

    def async_put(self, callback, key, **values):
        '''Asynchronous version of :meth:`put`.

        :Callback arguments:
            `store`: :class:`AbstractStore` instance
                Store instance
            `key`: string
                Name of the key to search for
            `result`: bool
                Indicate True if the storage has been updated, or False if
                nothing has been done (no changes). None if any error.
        '''
        self._schedule(self.store_put_async,
                       key=key, value=values, callback=callback)

    def delete(self, key):
        '''Delete a key from the storage. If the key is not found, a `KeyError`
        exception will be thrown.'''
        need_sync = self.store_delete(key)
        if need_sync:
            self.store_sync()
        return need_sync

    def async_delete(self, callback, key):
        '''Asynchronous version of :meth:`delete`.

        :Callback arguments:
            `store`: :class:`AbstractStore` instance
                Store instance
            `key`: string
                Name of the key to search for
            `result`: bool
                Indicate True if the storage has been updated, or False if
                nothing has been done (no changes). None if any error.
        '''
        self._schedule(self.store_delete_async, key=key,
                       callback=callback)

    def find(self, **filters):
        '''Return all the entries matching the filters. The entries are
        returned through a generator as a list of (key, entry) pairs
        where *entry* is a dict of key-value pairs ::

            for key, entry in store.find(name='Mathieu'):
                print('key:', key, ', entry:', entry)

        Because it's a generator, you cannot directly use it as a list. You can
        do::

            # get all the (key, entry) availables
            entries = list(store.find(name='Mathieu'))
            # get only the entry from (key, entry)
            entries = list((x[1] for x in store.find(name='Mathieu')))
        '''
        return self.store_find(filters)

    def async_find(self, callback, **filters):
        '''Asynchronous version of :meth:`find`.

        The callback will be called for each entry in the result.

        :Callback arguments:
            `store`: :class:`AbstractStore` instance
                Store instance
            `key`: string
                Name of the key to search for, or None if we reach the end of
                the results
            `result`: bool
                Indicate True if the storage has been updated, or False if
                nothing has been done (no changes). None if any error.
        '''
        self._schedule(self.store_find_async,
                       callback=callback, filters=filters)

    def keys(self):
        '''Return a list of all the keys in the storage.
        '''
        return self.store_keys()

    def async_keys(self, callback):
        '''Asynchronously return all the keys in the storage.
        '''
        self._schedule(self.store_keys_async, callback=callback)

    def count(self):
        '''Return the number of entries in the storage.
        '''
        return self.store_count()

    def async_count(self, callback):
        '''Asynchronously return the number of entries in the storage.
        '''
        self._schedule(self.store_count_async, callback=callback)

    def clear(self):
        '''Wipe the whole storage.
        '''
        return self.store_clear()

    def async_clear(self, callback):
        '''Asynchronous version of :meth:`clear`.
        '''
        self._schedule(self.store_clear_async, callback=callback)

    #
    # Operators
    #

    def __setitem__(self, key, values):
        if not isinstance(values, dict):
            raise Exception('Only dict are accepted for the store[key] = dict')
        self.put(key, **values)

    def __getitem__(self, key):
        return self.get(key)

    def __delitem__(self, key):
        return self.keys()

    def __contains__(self, key):
        return self.exists(key)

    def __len__(self):
        return self.count()

    def __iter__(self):
        for key in self.keys():
            yield key

    #
    # Used for implementation
    #

    def store_load(self):
        pass

    def store_sync(self):
        pass

    def store_get(self, key):
        raise NotImplementedError

    def store_put(self, key, value):
        raise NotImplementedError

    def store_exists(self, key):
        raise NotImplementedError

    def store_delete(self, key):
        raise NotImplementedError

    def store_find(self, filters):
        return []

    def store_keys(self):
        return []

    def store_count(self):
        return len(self.store_keys())

    def store_clear(self):
        for key in self.store_keys():
            self.store_delete(key)
        self.store_sync()

    def store_get_async(self, key, callback):
        try:
            value = self.store_get(key)
            callback(self, key, value)
        except KeyError:
            callback(self, key, None)

    def store_put_async(self, key, value, callback):
        try:
            value = self.put(key, **value)
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
            value = self.delete(key)
            callback(self, key, value)
        except:
            callback(self, key, None)

    def store_find_async(self, filters, callback):
        for key, entry in self.store_find(filters):
            callback(self, filters, key, entry)
        callback(self, filters, None, None)

    def store_count_async(self, callback):
        try:
            value = self.store_count()
            callback(self, value)
        except:
            callback(self, 0)

    def store_keys_async(self, callback):
        try:
            keys = self.store_keys()
            callback(self, keys)
        except:
            callback(self, [])

    def store_clear_async(self, callback):
        self.store_clear()
        callback(self)

    #
    # Privates
    #

    def _schedule(self, cb, **kwargs):
        # XXX not entirely sure about the best value (0 or -1).
        Clock.schedule_once(lambda dt: cb(**kwargs), 0)

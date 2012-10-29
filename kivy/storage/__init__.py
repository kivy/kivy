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
    store.put('key1', 'hello world')
    print 'key1 is', store.get('key1')

Because the data is persistant, i can check later if the key exists::

    from kivy.storage.jsonstore import JsonStore

    store = JsonStore('hello.json')
    if store.exists('key1'):
        print 'key1 exists, the value is', store.get('key1')
        store.delete('key1')


Synchronous / Asynchronous API
------------------------------

All the methods have a `callback` parameter. If set, the callback will be used
to return the result to the user when available: the request will be
asynchronous.  If the `callback` is None, then the request will be synchronous
and the result will be returned directly.


Without callback (Synchronous API)::

    result = mystore.get('plop')
    print 'the key plop have', result


With callback (Asynchronous API):

    def my_callback(key, value):
        print 'the key', key, 'have', value
    mystore.get('plop', callback=my_callback)

'''

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import OptionProperty, ListProperty
from json import dumps, loads
from base64 import b64encode, b64decode
from functools import partial


class AbstractStore(EventDispatcher):
    '''Abstract class used to implement a Store
    '''

    converter = OptionProperty('raw', options=(
        'raw', 'json', 'base64', 'user'))

    user_converter = ListProperty([None, None])

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

    def get(self, key, callback=None, converter=None):
        '''Get the value stored at `key`.

        For more information about the `callback`, read the module
        documentation.

        If the key is not found, an `KeyError` exception will be throw.
        '''
        if callback is None:
            raw_value = self.store_get(key)
            return self.decode_value(raw_value, converter=converter)
        self._schedule(self.store_get_async,
                key=key,
                callback=partial(self._store_get_decode,
                    callback=callback, converter=converter))

    def put(self, key, value, callback=None, converter=None):
        '''Put a new key/value in the storage

        For more information about the `callback`, read the module
        documentation.
        '''
        if callback is None:
            value = self.encode_value(value, converter=converter)
            need_sync = self.store_put(key, value)
            if need_sync:
                self.store_sync()
            return need_sync
        self._schedule(self.store_put_async,
                key=key, value=value, callback=callback)

    def delete(self, key, callback=None):
        '''Delete a key from the storage.

        For more information about the `callback`, read the module
        documentation.

        If the key is not found, an `KeyError` exception will be throw.
        '''
        if callback is None:
            need_sync = self.store_delete(key)
            if need_sync:
                self.store_sync()
            return need_sync
        self._schedule(self.store_delete, key=key,
                callback=callback)


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

    def encode_value(self, value, converter):
        '''(internal) Method used to encode a value with a specific converter.
        This method is used internally by the Store.
        '''
        if converter is None:
            converter = self.converter
        if converter == 'raw':
            return value
        elif converter == 'json':
            return dumps(value)
        elif converter == 'base64':
            return b64encode(value)
        elif converter == 'user':
            return self.user_converter[0](value)
        raise NameError('Invalid converter {0}'.format(converter))

    def decode_value(self, value, converter):
        '''(internal) Method used to encode a value with a specific converter
        This method is used internally by the Store.
        '''
        if converter is None:
            converter = self.converter
        if converter == 'raw':
            return value
        elif converter == 'json':
            return loads(value)
        elif converter == 'base64':
            return b64decode(value)
        elif converter == 'user':
            return self.user_converter[1](value)
        raise NameError('Invalid converter {0}'.format(converter))

    #
    # Privates
    #

    def _schedule(self, callback, **kwargs):
        # XXX not entirely sure about the best value (0 or -1).
        Clock.schedule_once(partial(callback, **kwargs), 0)

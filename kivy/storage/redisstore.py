'''
Redis Store
===========

Store implementation using Redis. You must have redis-py installed.

Usage example::

    from kivy.storage.redisstore import RedisStore

    params = dict(host='localhost', port=6379, db=14)
    store = RedisStore(params)

All the key-value pairs will be stored with a prefix 'store' by default.
You can instanciate the storage with another prefix like this::


    from kivy.storage.redisstore import RedisStore

    params = dict(host='localhost', port=6379, db=14)
    store = RedisStore(params, prefix='mystore2')

The params dictionary will be passed to the redis.StrictRedis class.

See `redis-py <https://github.com/andymccurdy/redis-py>`_.
'''

__all__ = ('RedisStore', )

import os
from json import loads, dumps
from kivy.properties import StringProperty
from kivy.storage import AbstractStore

# don't import redis during the documentation generation
if 'KIVY_DOC' not in os.environ:
    import redis


class RedisStore(AbstractStore):
    '''Store implementation using a Redis database.
    See the :mod:`kivy.storage` module documentation for more informations.
    '''

    prefix = StringProperty('store')

    def __init__(self, redis_params, **kwargs):
        self.redis_params = redis_params
        self.r = None
        super(RedisStore, self).__init__(**kwargs)

    def store_load(self):
        self.r = redis.StrictRedis(**self.redis_params)

    def store_sync(self):
        pass

    def store_exists(self, key):
        key = self.prefix + '.d.' + key
        value = self.r.exists(key)
        return value

    def store_get(self, key):
        key = self.prefix + '.d.' + key
        if not self.r.exists(key):
            raise KeyError(key)
        result = self.r.hgetall(key)
        for k in result.keys():
            result[k] = loads(result[k])
        return result

    def store_put(self, key, values):
        key = self.prefix + '.d.' + key
        pipe = self.r.pipeline()
        pipe.delete(key)
        for k, v in values.iteritems():
            pipe.hset(key, k, dumps(v))
        pipe.execute()
        return True

    def store_delete(self, key):
        key = self.prefix + '.d.' + key
        if not self.r.exists(key):
            raise KeyError(key)
        return self.r.delete(key)

    def store_keys(self):
        l = len(self.prefix + '.d.')
        return [x[l:] for x in self.r.keys(self.prefix + '.d.*')]

    def store_find(self, filters):
        fkeys = filters.keys()
        fvalues = filters.values()
        for key in self.store_keys():
            skey = self.prefix + '.d.' + key
            svalues = self.r.hmget(skey, fkeys)
            if None in svalues:
                continue
            svalues = [loads(x) for x in svalues]
            if fvalues != svalues:
                continue
            yield key, self.r.hgetall(skey)

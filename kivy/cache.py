'''
Cache manager
=============

The cache manager can be used to store python objects attached to a unique
key. The cache can be controlled in two ways: with a object limit or a
timeout.

For example, we can create a new cache with a limit of 10 objects and a
timeout of 5 seconds::

    # register a new Cache
    Cache.register('mycache', limit=10, timeout=5)

    # create an object + id
    key = 'objectid'
    instance = Label(text=text)
    Cache.append('mycache', key, instance)

    # retrieve the cached object
    instance = Cache.get('mycache', key)

If the instance is NULL, the cache may have trashed it because you've
not used the label for 5 seconds and you've reach the limit.
'''

__all__ = ('Cache', )

from os import environ
from kivy.logger import Logger
from kivy.clock import Clock


class Cache(object):
    '''See module documentation for more information.
    '''

    _categories = {}
    _objects = {}

    @staticmethod
    def register(category, limit=None, timeout=None, max_size=None,
                 compute_size=None):
        '''Register a new category in the cache with the specified limit.

        :Parameters:
            `category`: str
                Identifier of the category.
            `limit`: int (optional)
                Maximum number of objects allowed in the cache.
                If None, no limit is applied.
            `timeout`: double (optional)
                Time after which to delete the object if it has not been used.
                If None, no timeout is applied.
            `max_size`: maximum memory to be used by the cache.
                If None, no limit is applied.
                This require the `compute_size` argument to be set.
                .. versionadded:: 1.9.2
            `compute_size`: a function to compute the size of an object
                in cache.  current size of the cache will be updated
                whenever an object is added/removed using this function
                on the object. If max_size is > 0, this method will be
                called every time an object is added, so it must be fast
                enough.
                .. versionadded:: 1.9.2
        '''
        Cache._categories[category] = {
            'limit': limit,
            'timeout': timeout,
            'max_size': max_size,
            'compute_size': compute_size,
            'sizes': {},
            'size': 0}
        Cache._objects[category] = {}
        Logger.debug(
            'Cache: register <%s> with limit=%s, timeout=%s, '
            'max_size=%s, compute_size=%s' % (
                category, str(limit), str(timeout), str(max_size),
                str(compute_size)))

    @staticmethod
    def append(category, key, obj, timeout=None):
        '''Add a new object to the cache.

        :Parameters:
            `category`: str
                Identifier of the category.
            `key`: str
                Unique identifier of the object to store.
            `obj`: object
                Object to store in cache.
            `timeout`: double (optional)
                Time after which to delete the object if it has not been used.
                If None, no timeout is applied.
        '''
        Logger.trace('appending %s to Cache %s', key, category)
        #check whether obj should not be cached first
        if getattr(obj, '_no_cache', False):
            return
        try:
            cat = Cache._categories[category]
        except KeyError:
            Logger.warning('Cache: category <%s> does not exist' % category)
            return
        timeout = timeout or cat['timeout']

        limit = cat['limit']
        if limit is not None and len(Cache._objects[category]) >= limit:
            Cache._purge_oldest(category)

        if cat['max_size']:
            object_size = cat['compute_size'](obj)
            Logger.trace('object size is %s', object_size)
            cat['size'] += object_size
            if key in Cache._objects[category]:
                # old value is being overwritten, so we need to
                # substract its size first
                cat['size'] -= cat['sizes'][key]
            cat['sizes'][key] = object_size

            while cat['size'] > cat['max_size']:
                Logger.trace("%s size %s", category, cat['size'])
                if not Cache._purge_oldest(category):
                    Logger.warning('new cache size %s', cat['size'])
                    break
                Logger.trace('new cache size %s', cat['size'])

        Cache._objects[category][key] = {
            'object': obj,
            'timeout': timeout,
            'lastaccess': Clock.get_time(),
            'timestamp': Clock.get_time()}

    @staticmethod
    def get(category, key, default=None):
        '''Get a object from the cache.

        :Parameters:
            `category`: str
                Identifier of the category.
            `key`: str
                Unique identifier of the object in the store.
            `default`: anything, defaults to None
                Default value to be returned if the key is not found.
        '''
        try:
            Cache._objects[category][key]['lastaccess'] = Clock.get_time()
            return Cache._objects[category][key]['object']
        except Exception:
            return default

    @staticmethod
    def get_timestamp(category, key, default=None):
        '''Get the object timestamp in the cache.

        :Parameters:
            `category`: str
                Identifier of the category.
            `key`: str
                Unique identifier of the object in the store.
            `default`: anything, defaults to None
                Default value to be returned if the key is not found.
        '''
        try:
            return Cache._objects[category][key]['timestamp']
        except Exception:
            return default

    @staticmethod
    def get_lastaccess(category, key, default=None):
        '''Get the objects last access time in the cache.

        :Parameters:
            `category`: str
                Identifier of the category.
            `key`: str
                Unique identifier of the object in the store.
            `default`: anything, defaults to None
                Default value to be returned if the key is not found.
        '''
        try:
            return Cache._objects[category][key]['lastaccess']
        except Exception:
            return default

    @staticmethod
    def remove(category, key=None):
        '''Purge the cache.

        :Parameters:
            `category`: str
                Identifier of the category.
            `key`: str (optional)
                Unique identifier of the object in the store. If this
                argument is not supplied, the entire category will be purged.
        '''
        Logger.trace("trying to remove %s from %s", key, category)
        if key is not None:
            cat = Cache._categories[category]
            Logger.trace('cat max size %s', cat['max_size'])
            if cat['max_size']:
                obj_size = cat['sizes'][key]
                Logger.trace('removing %s from %s size: %s',
                             obj_size, category, obj_size)
                cat['size'] -= obj_size
                del cat['sizes'][key]

            del Cache._objects[category][key]
            Logger.trace("removed %s:%s from cache", category, key)
        else:
            Cache._objects[category] = {}
            Logger.trace("flushed category %s from cache", category)

    @staticmethod
    def _purge_oldest(category, maxpurge=1):
        Logger.debug('PURGE %s', category)
        import heapq
        heap_list = []
        time = Clock.get_time()
        for key in Cache._objects[category]:
            obj = Cache._objects[category][key]
            if obj['lastaccess'] == obj['timestamp'] == time:
                Logger.trace("ignoring %s", obj)
                continue

            heapq.heappush(heap_list, (obj['lastaccess'], key))
            Logger.debug('<<< %s %s', obj, obj['lastaccess'])

        n = 0
        while n < maxpurge:
            n += 1
            if not heap_list:
                Logger.warning('unable to reduce Cache %s', category)
                return False
            lastaccess, key = heapq.heappop(heap_list)
            Logger.debug('=> %s %s %s', key, lastaccess, Clock.get_time())
            Cache.remove(category, key)

    @staticmethod
    def _purge_by_timeout(dt):
        curtime = Clock.get_time()

        for category in Cache._objects:
            if category not in Cache._categories:
                continue
            timeout = Cache._categories[category]['timeout']
            if timeout is not None and dt > timeout:
                # XXX got a lag ! that may be because the frame take lot of
                # time to draw. and the timeout is not adapted to the current
                # framerate. So, increase the timeout by two.
                # ie: if the timeout is 1 sec, and framerate go to 0.7, newly
                # object added will be automatically trashed.
                timeout *= 2
                Cache._categories[category]['timeout'] = timeout
                continue

            for key in list(Cache._objects[category].keys())[:]:
                lastaccess = Cache._objects[category][key]['lastaccess']
                objtimeout = Cache._objects[category][key]['timeout']

                # take the object timeout if available
                if objtimeout is not None:
                    timeout = objtimeout

                # no timeout, cancel
                if timeout is None:
                    continue

                if curtime - lastaccess > timeout:
                    Cache.remove(category, key)

    @staticmethod
    def print_usage():
        '''Print the cache usage to the console.'''
        print('Cache usage :')
        for category in Cache._categories:
            print(' * %s : %d / %s, timeout=%s' % (
                category.capitalize(),
                len(Cache._objects[category]),
                str(Cache._categories[category]['limit']),
                str(Cache._categories[category]['timeout'])))

if 'KIVY_DOC_INCLUDE' not in environ:
    # install the schedule clock for purging
    Clock.schedule_interval(Cache._purge_by_timeout, 1)

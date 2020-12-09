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

from os import environ
from kivy.logger import Logger
from kivy.clock import Clock

__all__ = ('Cache', )


class Cache(object):
    '''See module documentation for more information.
    '''

    _categories = {}
    _objects = {}

    @staticmethod
    def register(category, limit=None, timeout=None):
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
        '''
        Cache._categories[category] = {
            'limit': limit,
            'timeout': timeout}
        Cache._objects[category] = {}
        Logger.debug(
            'Cache: register <%s> with limit=%s, timeout=%s' %
            (category, str(limit), str(timeout)))

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

        :raises:
            `ValueError`: If `None` is used as `key`.

        .. versionchanged:: 2.0.0
            Raises `ValueError` if `None` is used as `key`.

        '''
        # check whether obj should not be cached first
        if getattr(obj, '_nocache', False):
            return
        if key is None:
            # This check is added because of the case when key is None and
            # one of purge methods gets called. Then loop in purge method will
            # call Cache.remove with key None which then clears entire
            # category from Cache making next iteration of loop to raise a
            # KeyError because next key will not exist.
            # See: https://github.com/kivy/kivy/pull/6950
            raise ValueError('"None" cannot be used as key in Cache')
        try:
            cat = Cache._categories[category]
        except KeyError:
            Logger.warning('Cache: category <%s> does not exist' % category)
            return

        timeout = timeout or cat['timeout']

        limit = cat['limit']

        if limit is not None and len(Cache._objects[category]) >= limit:
            Cache._purge_oldest(category)

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
        try:
            if key is not None:
                del Cache._objects[category][key]
                Logger.trace('Cache: Removed %s:%s from cache' %
                             (category, key))
            else:
                Cache._objects[category] = {}
                Logger.trace('Cache: Flushed category %s from cache' %
                             category)
        except Exception:
            pass

    @staticmethod
    def _purge_oldest(category, maxpurge=1):
        Logger.trace('Cache: Remove oldest in %s' % category)
        import heapq
        time = Clock.get_time()
        heap_list = []
        for key in Cache._objects[category]:
            obj = Cache._objects[category][key]
            if obj['lastaccess'] == obj['timestamp'] == time:
                continue
            heapq.heappush(heap_list, (obj['lastaccess'], key))
            Logger.trace('Cache: <<< %f' % obj['lastaccess'])
        n = 0
        while n <= maxpurge:
            try:
                n += 1
                lastaccess, key = heapq.heappop(heap_list)
                Logger.trace('Cache: %d => %s %f %f' %
                             (n, key, lastaccess, Clock.get_time()))
            except Exception:
                return
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

            for key in list(Cache._objects[category].keys()):
                lastaccess = Cache._objects[category][key]['lastaccess']
                objtimeout = Cache._objects[category][key]['timeout']

                # take the object timeout if available
                if objtimeout is not None:
                    timeout = objtimeout

                # no timeout, cancel
                if timeout is None:
                    continue

                if curtime - lastaccess > timeout:
                    Logger.trace('Cache: Removed %s:%s from cache due to '
                                 'timeout' % (category, key))
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

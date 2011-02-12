'''
Cache manager
=============

The cache manager can be used to store python object attached to an uniq key.
The cache can be controlled in different manner, with a object limit or a
timeout.

For example, we can create a new cache with a limit of 10 objects and a timeout
of 5 seconds::

    # register a new Cache
    Cache.register('mycache', limit=10, timeout=5)

    # create an object + id
    text = 'objectid'
    instance = Label(text=text)
    Cache.append('mycache', text, instance)

    # retrieve the cached object
    instance = Cache.get('mycache', label)

If the instance is NULL, the cache may have trash it, because you've
not used the label since 5 seconds, and you've reach the limit.
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
    def register(category, limit=None, timeout=None):
        '''Register a new category in cache, with limit

        :Parameters:
            `category` : str
                Identifier of the category
            `limit` : int (optionnal)
                Maximum number of object in the cache.
                If None, no limit is applied.
            `timeout` : double (optionnal)
                Time to delete the object when it's not used.
                if None, no timeout is applied.
        '''
        Cache._categories[category] = {
            'limit': limit,
            'timeout': timeout}
        Cache._objects[category] = {}
        Logger.debug('Cache: register <%s> with limit=%s, timeout=%ss' %
            (category, str(limit), str(timeout)))

    @staticmethod
    def append(category, key, obj, timeout=None):
        '''Add a new object in the cache.

        :Parameters:
            `category` : str
                Identifier of the category
            `key` : str
                Uniq identifier of the object to store
            `obj` : object
                Object to store in cache
            `timeout` : double (optionnal)
                Custom time to delete the object if it's not used.
        '''
        try:
            cat = Cache._categories[category]
        except KeyError:
            Logger.warning('Cache: category <%s> not exist' % category)
            return
        timeout = timeout or cat['timeout']
        # FIXME: activate purge when limit is hit
        #limit = cat['limit']
        #if limit is not None and len(Cache._objects[category]) >= limit:
        #    Cache._purge_oldest(category)
        Cache._objects[category][key] = {
            'object': obj,
            'timeout': timeout,
            'lastaccess': Clock.get_time(),
            'timestamp': Clock.get_time()}

    @staticmethod
    def get(category, key, default=None):
        '''Get a object in cache.

        :Parameters:
            `category` : str
                Identifier of the category
            `key` : str
                Uniq identifier of the object to store
            `default` : anything, default to None
                Default value to be returned if key is not found
        '''
        try:
            Cache._objects[category][key]['lastaccess'] = Clock.get_time()
            return Cache._objects[category][key]['object']
        except Exception:
            return default

    @staticmethod
    def get_timestamp(category, key, default=None):
        '''Get the object timestamp in cache.

        :Parameters:
            `category` : str
                Identifier of the category
            `key` : str
                Uniq identifier of the object to store
            `default` : anything, default to None
                Default value to be returned if key is not found
        '''
        try:
            return Cache._objects[category][key]['timestamp']
        except Exception:
            return default

    @staticmethod
    def get_lastaccess(category, key, default=None):
        '''Get the object last access time in cache.

        :Parameters:
            `category` : str
                Identifier of the category
            `key` : str
                Uniq identifier of the object to store
            `default` : anything, default to None
                Default value to be returned if key is not found
        '''
        try:
            return Cache._objects[category][key]['lastaccess']
        except Exception:
            return default

    @staticmethod
    def remove(category, key=None):
        '''Purge the cache

        :Parameters:
            `category` : str (optionnal)
                Identifier of the category
            `key` : str (optionnal)
                Uniq identifier of the object to store
        '''
        try:
            if key is not None:
                del Cache._objects[category][key]
            else:
                Cache._objects[category] = {}
        except Exception:
            pass

    @staticmethod
    def _purge_oldest(category, maxpurge=1):
        print 'PURGE', category
        import heapq
        heap_list = []
        for key in Cache._objects[category]:
            obj = Cache._objects[category][key]
            if obj['lastaccess'] == obj['timestamp']:
                continue
            heapq.heappush(heap_list, (obj['lastaccess'], key))
            print '<<<', obj['lastaccess']
        n = 0
        while n < maxpurge:
            try:
                lastaccess, key = heapq.heappop(heap_list)
                print '=>', key, lastaccess, Clock.get_time()
            except Exception:
                return
            del Cache._objects[category][key]

    @staticmethod
    def _purge_by_timeout(dt):
        curtime = Clock.get_time()

        for category in Cache._objects:
            timeout = Cache._categories[category]['timeout']
            if timeout is not None and dt > timeout:
                # XXX got a lag ! that may be because the frame take lot of
                # time to draw. and the timeout is not adapted to the current
                # framerate. So, increase the timeout by two.
                # ie: if the timeout is 1 sec, and framerate go to 0.7, newly
                # object added will be automaticly trashed.
                timeout *= 2
                Cache._categories[category]['timeout'] = timeout
                continue

            for key in Cache._objects[category].keys()[:]:
                lastaccess = Cache._objects[category][key]['lastaccess']
                objtimeout = Cache._objects[category][key]['timeout']

                # take the object timeout if available
                if objtimeout is not None:
                    timeout = objtimeout

                # no timeout, cancel
                if timeout is None:
                    continue

                if curtime - lastaccess > timeout:
                    del Cache._objects[category][key]

    @staticmethod
    def print_usage():
        '''Print the cache usage on the console'''
        print 'Cache usage :'
        for category in Cache._categories:
            print ' * %s : %d / %s, timeout=%s' % (
                category.capitalize(),
                len(Cache._objects[category]),
                str(Cache._categories[category]['limit']),
                str(Cache._categories[category]['timeout']))

if 'KIVY_DOC_INCLUDE' not in environ:
    # install the schedule clock for purging
    Clock.schedule_interval(Cache._purge_by_timeout, 1)

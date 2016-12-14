'''
Cache tests
===========
'''

import unittest


def get_size(x):
    return x


class CacheTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.cache import Cache
        Cache.register('test_simple')
        Cache.register('test_limit', limit=10)
        Cache.register('test_max_size', max_size=10, compute_size=get_size)

    def test_set_get(self):
        from kivy.cache import Cache
        a = 1
        Cache.append('test_simple', '1', a)
        assert Cache.get('test_simple', '1') == a

    def test_limit(self):
        from kivy.cache import Cache
        from kivy.clock import Clock

        for i in range(10):
            Cache.append('test_limit', str(i), i)

        for i in range(10):
            Clock.tick()
            v = Cache.get('test_limit', str(i))
            assert v == i

        Cache.append('test_limit', '11', 11)
        assert Cache.get('test_limit', '0') is None

    def test_max_size(self):
        from kivy.cache import Cache
        from kivy.clock import Clock

        for i in range(10):
            Cache.append('test_max_size', str(i), i)
            Clock.tick()

        for i in range(10):
            Clock.tick()
            if Cache.get('test_max_size', str(i)) is None:
                break
        else:
            print(Cache._categories['test_max_size'])
            assert False

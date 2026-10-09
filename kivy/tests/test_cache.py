import unittest
from unittest.mock import patch

from kivy.cache import Cache


class CachePurgeTest(unittest.TestCase):

    def setUp(self):
        self.category = 'test.cache.purge.count'
        Cache.register(self.category, limit=2)
        self.time = 0
        self.clock = patch('kivy.cache.Clock.get_time',
                           side_effect=lambda: self.time)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.addCleanup(Cache._objects.pop, self.category, None)
        self.addCleanup(Cache._categories.pop, self.category, None)

    def append(self, key, time):
        self.time = time
        Cache.append(self.category, key, key)

    def test_append_evicts_only_one_oldest_entry(self):
        self.append('a', 1)
        self.append('b', 2)
        self.append('c', 3)
        self.assertIsNone(Cache.get(self.category, 'a'))
        self.assertEqual(Cache.get(self.category, 'b'), 'b')
        self.assertEqual(Cache.get(self.category, 'c'), 'c')

    def test_repeated_appends_retain_capacity(self):
        for index in range(1, 8):
            self.append(str(index), index)
            expected = {str(key) for key in range(max(1, index - 1), index + 1)}
            self.assertEqual(set(Cache._objects[self.category]), expected)

    def test_recent_access_protects_older_entry(self):
        self.append('a', 1)
        self.append('b', 2)
        self.time = 3
        self.assertEqual(Cache.get(self.category, 'a'), 'a')
        self.append('c', 4)
        self.assertEqual(set(Cache._objects[self.category]), {'a', 'c'})

    def test_explicit_purge_count(self):
        Cache._categories[self.category]['limit'] = None
        for index, key in enumerate(('a', 'b', 'c', 'd'), 1):
            self.append(key, index)
        self.time = 5
        Cache._purge_oldest(self.category, maxpurge=2)
        self.assertEqual(set(Cache._objects[self.category]), {'c', 'd'})

    def test_zero_purge_keeps_entries(self):
        self.append('a', 1)
        self.time = 2
        Cache._purge_oldest(self.category, maxpurge=0)
        self.assertEqual(Cache.get(self.category, 'a'), 'a')

    def test_current_frame_entry_is_protected(self):
        self.append('a', 1)
        Cache._purge_oldest(self.category)
        self.assertEqual(Cache.get(self.category, 'a'), 'a')

    def test_empty_purge_is_safe(self):
        Cache._purge_oldest(self.category, maxpurge=2)
        self.assertEqual(Cache._objects[self.category], {})


if __name__ == '__main__':
    unittest.main()

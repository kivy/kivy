'''
utils tests
===========
'''

import os
import unittest
try:
    from unittest.mock import patch   # python 3.x
except:
    from mock import patch   # python 2.x

from kivy.utils import (boundary, escape_markup, format_bytes_to_human,
        is_color_transparent, SafeList, get_random_color, get_hex_from_color,
        get_color_from_hex, strtotuple, QueryDict, intersection, difference,
        interpolate, _get_platform, deprecated, reify)
from kivy import utils


class UtilsTest(unittest.TestCase):

    def test_escape_markup(self):
        escaped = escape_markup('Sun [1] & Moon [2].')
        self.assertEqual(escaped, 'Sun &bl;1&br; &amp; Moon &bl;2&br;.')

    def test_format_bytes_to_human(self):
        a = format_bytes_to_human(6463)
        self.assertEqual(a, '6.31 KB')
        b = format_bytes_to_human(6463, precision=4)
        self.assertEqual(b, '6.3115 KB')
        c = format_bytes_to_human(646368746541)
        self.assertEqual(c, '601.98 GB')

    def test_boundary(self):
        x = boundary(-1000, 0, 100)
        self.assertEqual(x, 0)
        x = boundary(1000, 0, 100)
        self.assertEqual(x, 100)
        x = boundary(50, 0, 100)
        self.assertEqual(x, 50)

    def test_is_color_transparent(self):
        c = [1, 1, 1]
        self.assertFalse(is_color_transparent(c))
        c = [1, 1, 1, 1]
        self.assertFalse(is_color_transparent(c))
        c = [1, 1, 1, 0]
        self.assertTrue(is_color_transparent(c))

    @deprecated
    def a_deprecated_function(self):
        """ This one has doc string. """
        pass

    def test_deprecated(self):
        self.a_deprecated_function()

    def test_SafeList_iterate(self):  # deprecated
        sl = SafeList(['1', 2, 3.])
        self.assertTrue(isinstance(sl, list))
        it = sl.iterate()
        self.assertEqual(next(it), '1')
        self.assertEqual(next(it), 2)
        self.assertEqual(next(it), 3.)

    def test_SafeList_iterate_reverse(self):  # deprecated
        sl = SafeList(['1', 2, 3.])
        self.assertTrue(isinstance(sl, list))
        it = sl.iterate(reverse=True)
        self.assertEqual(next(it), 3.)
        self.assertEqual(next(it), 2)
        self.assertEqual(next(it), '1')

    def test_SafeList_clear(self):
        sl = SafeList(['1', 2, 3.])
        self.assertTrue(isinstance(sl, list))
        sl.clear()
        self.assertEqual(len(sl), 0)

    def test_get_random_color_fixed_alpha(self):
        actual = get_random_color()
        self.assertEqual(len(actual), 4)
        self.assertEqual(actual[3], 1.)

        actual = get_random_color(alpha=.5)
        self.assertEqual(len(actual), 4)
        self.assertEqual(actual[3], .5)

    def test_get_random_color_random_alpha(self):
        actual = get_random_color(alpha='random')
        self.assertEqual(len(actual), 4)

    def test_get_hex_from_color_noalpha(self):
        actual = get_hex_from_color([0, 1, 0])
        expected = '#00ff00'
        self.assertEqual(actual, expected)

    def test_get_hex_from_color_alpha(self):
        actual = get_hex_from_color([.25, .77, .90, .5])
        expected = '#3fc4e57f'
        self.assertEqual(actual, expected)

    def test_get_color_from_hex_noalpha(self):
        actual = get_color_from_hex('#d1a9c4')
        expected = [0.81960784, 0.66274509, 0.76862745, 1.]
        for i in range(4):
            self.assertAlmostEqual(actual[i], expected[i])

    def test_get_color_from_hex_alpha(self):
        actual = get_color_from_hex('#00FF7F7F')
        expected = [0., 1., 0.49803921, 0.49803921]  # can't get .5 from hex
        for i in range(4):
            self.assertAlmostEqual(actual[i], expected[i])

    def test_strtotuple(self):
        self.assertRaises(Exception, strtotuple, 'adis!_m%*+-=|')
        self.assertRaises(Exception, strtotuple, '((12, 8, 473)')
        self.assertRaises(Exception, strtotuple, '[12, 8, 473]]')
        self.assertRaises(Exception, strtotuple, '128473')
        actual = strtotuple('(12, 8, 473)')
        expected = (12, 8, 473)
        self.assertEqual(actual, expected)

    def test_QueryDict(self):
        qd = QueryDict()
        self.assertTrue(isinstance(qd, dict))
        # __setattr__
        qd.toto = 1
        self.assertEqual(qd.get('toto'), 1)
        # __getattr__
        toto = qd.toto
        self.assertEqual(toto, 1)
        with self.assertRaises(AttributeError):
            foo = qd.not_an_attribute

    def test_intersection(self):
        abcd = ['a', 'b', 'c', 'd']
        efgh = ['e', 'f', 'g', 'h']
        fedc = ['c', 'd', 'e', 'f']  # cdef is cython keyword O_o)
        feed = ['f', 'e', 'e', 'd']
        self.assertEqual(intersection(abcd, efgh), [])
        self.assertEqual(intersection(abcd, fedc), ['c', 'd'])
        self.assertEqual(intersection(feed, feed), feed)
        self.assertEqual(intersection([], []), [])
        self.assertEqual(intersection(feed, fedc), feed)
        self.assertEqual(intersection(fedc, feed), ['d', 'e', 'f'])
        self.assertEqual(intersection(feed, efgh), ['f', 'e', 'e'])

    def test_difference(self):
        abcd = ['a', 'b', 'c', 'd']
        efgh = ['e', 'f', 'g', 'h']
        fedc = ['c', 'd', 'e', 'f']  # cdef is cython keyword O_o
        feed = ['f', 'e', 'e', 'd']
        self.assertEqual(difference(abcd, efgh), ['a', 'b', 'c', 'd'])
        self.assertEqual(difference(efgh, fedc), ['g', 'h'])
        self.assertEqual(difference([], []), [])
        self.assertEqual(difference(abcd, abcd), [])
        self.assertEqual(difference(fedc, feed), ['c'])
        self.assertEqual(difference(feed, abcd), ['f', 'e', 'e'])
        self.assertEqual(difference(abcd, feed), ['a', 'b', 'c'])

    def test_interpolate_solo(self):
        values = [10., 19., 27.1]
        a = 0.
        for i in range(0, 3):
            a = interpolate(a, 100)
            self.assertEqual(a, values[i])

    def test_interpolate_multi(self):
        x = [10., 19., 27.1]
        y = [-10., -19., -27.1]
        p = 0., 0.
        for i in range(0, 3):
            p = interpolate(p, [100, -100])
            self.assertEqual(p, [x[i], y[i]])

    @reify
    def fib_100(self):
        """ return 100th Fibonacci number
        This uses modern view of F sub 1 = 0, F sub 2 = 1. """
        # print "calculating..."
        a, b = 0, 1
        for n in range(2, 101):
            a, b = b, a + b
        return b

    def test_reify(self):
        first = self.fib_100   # slow. self.fib_100 is a reify object making
                               # the lazy call.
        second = self.fib_100  # fast, self.fib_100 is a long.
        assert first == second

    def test_Platform_android(self):
        with patch.dict('os.environ', {'ANDROID_ARGUMENT': ''}):
            pf = _get_platform()
            self.assertTrue(pf == 'android')
        self.assertNotIn('ANDROID_ARGUMENT', os.environ)

    def test_Platform_ios(self):
        with patch.dict('os.environ', {'KIVY_BUILD': 'ios'}):
            pf = _get_platform()
            self.assertEqual(pf, 'ios')
        self.assertNotIn('KIVY_BUILD', os.environ)

    def test_Platform_win32(self):
        self._test_platforms('win32', 'win')

    def test_Platform_cygwin(self):
        self._test_platforms('cygwin', 'win')

    def test_Platform_linux2(self):
        self._test_platforms('linux2', 'linux')

    def test_Platform_darwin(self):
        self._test_platforms('darwin', 'macosx')

    def test_Platform_freebsd(self):
        self._test_platforms('freebsd', 'linux')

    def test_Platform_unknown(self):
        self._test_platforms('randomdata', 'unknown')

    def _test_platforms(self, input, testval):
        utils._sys_platform = input
        pf = _get_platform()
        self.assertTrue(pf == testval)
        # with patch('kivy.utils._sys_platform') as m:
        #     m.__str__.return_value = input
        #     m.__eq__ = lambda x, y: str(x) == y
        #     pf = _get_platform()
        #     self.assertTrue(str(pf) == testval)

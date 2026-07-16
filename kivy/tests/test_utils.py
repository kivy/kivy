'''
utils tests
===========
'''

import os
import unittest
from unittest.mock import patch

from kivy.utils import (boundary, escape_markup, format_bytes_to_human,
        is_color_transparent, SafeList, get_random_color, get_hex_from_color,
        get_color_from_hex, strtotuple, QueryDict, intersection, difference,
        interpolate, _get_platform, deprecated, reify, normalize_path_id)
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
        # print("calculating...")
        a, b = 0, 1
        for n in range(2, 101):
            a, b = b, a + b
        return b

    def test_reify(self):
        # slow. self.fib_100 is a reify object making the lazy call.
        first = self.fib_100
        second = self.fib_100  # fast, self.fib_100 is a long.
        assert first == second

    def test_Platform_android(self):
        with patch.dict('os.environ', {'KIVY_BUILD': 'android'}):
            self.assertEqual(_get_platform(), 'android')
        self.assertNotIn('KIVY_BUILD', os.environ)

    def test_Platform_android_with_p4a(self):
        with patch.dict('os.environ', {'P4A_BOOTSTRAP': 'sdl3'}):
            self.assertEqual(_get_platform(), 'android')
        self.assertNotIn('P4A_BOOTSTRAP', os.environ)

    def test_Platform_android_with_android_argument(self):
        with patch.dict('os.environ', {'ANDROID_ARGUMENT': ''}):
            self.assertEqual(_get_platform(), 'android')
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

    def test_normalize_path_id_spaces(self):
        # Spaces should be replaced with underscores
        result = normalize_path_id("My Photo Editor")
        self.assertEqual(result, "My_Photo_Editor")

    def test_normalize_path_id_invalid_chars(self):
        # Invalid filesystem characters should be replaced
        result = normalize_path_id("Name:With*Invalid?Chars")
        self.assertEqual(result, "Name_With_Invalid_Chars")

        result = normalize_path_id('Path/With\\Slashes')
        self.assertEqual(result, "Path_With_Slashes")

    def test_normalize_path_id_unicode(self):
        # Unicode letters should be preserved
        result = normalize_path_id("Café Editor")
        self.assertEqual(result, "Café_Editor")

        result = normalize_path_id("日本語アプリ")
        self.assertEqual(result, "日本語アプリ")

    def test_normalize_path_id_control_chars(self):
        # Control characters should be removed
        result = normalize_path_id("Name\x00\x1F\x7FTest")
        self.assertEqual(result, "NameTest")

    def test_normalize_path_id_reserved_names(self):
        # Windows reserved names should be prefixed
        result = normalize_path_id("COM1")
        self.assertEqual(result, "_COM1")

        result = normalize_path_id("PRN")
        self.assertEqual(result, "_PRN")

        # Reserved name with suffix is safe
        result = normalize_path_id("COM1 Tool")
        self.assertEqual(result, "COM1_Tool")

    def test_normalize_path_id_strip(self):
        # Leading/trailing underscores, dots, spaces should be stripped
        result = normalize_path_id("  App Name  ")
        self.assertEqual(result, "App_Name")

        result = normalize_path_id("...App...")
        self.assertEqual(result, "App")

    def test_normalize_path_id_empty(self):
        # Empty or whitespace-only should raise ValueError
        with self.assertRaises(ValueError):
            normalize_path_id("")

        with self.assertRaises(ValueError):
            normalize_path_id("   ")

        # Only special chars that get removed
        with self.assertRaises(ValueError):
            normalize_path_id("///")

    def test_normalize_path_id_unicode_normalization(self):
        # Test NFC normalization - decomposed form should match composed
        # "é" as single character (NFC)
        nfc = normalize_path_id("Café")
        # "é" as e + combining acute accent (NFD)
        nfd = normalize_path_id("Cafe\u0301")
        self.assertEqual(nfc, nfd, "NFC normalization should make both equal")
        self.assertEqual(nfc, "Café")

    def test_normalize_path_id_zero_width_chars(self):
        # Zero-width space (U+200B) and other format chars should be removed
        result = normalize_path_id("My\u200BApp")  # zero-width space
        self.assertEqual(result, "MyApp")

        result = normalize_path_id("App\u200CName")  # zero-width non-joiner
        self.assertEqual(result, "AppName")

        result = normalize_path_id("Test\u200EApp")  # left-to-right mark
        self.assertEqual(result, "TestApp")

    def test_normalize_path_id_length_limit(self):
        # Long strings should be limited to 120 characters
        long_name = "A" * 150
        result = normalize_path_id(long_name)
        self.assertEqual(len(result), 120)
        self.assertEqual(result, "A" * 120)

        # Test with trailing underscores after truncation
        long_with_underscore = "A" * 119 + "___"
        result = normalize_path_id(long_with_underscore)
        self.assertLessEqual(len(result), 120)
        self.assertFalse(result.endswith("_"))

        # Unicode string length test
        long_unicode = "日" * 150
        result = normalize_path_id(long_unicode)
        self.assertEqual(len(result), 120)

    def test_normalize_path_id_emoji_removed(self):
        # Emoji should be replaced with underscores (not in \w)
        result = normalize_path_id("My App 🎨")
        self.assertEqual(result, "My_App")

        result = normalize_path_id("Photo📸Editor")
        self.assertEqual(result, "Photo_Editor")

    def test_normalize_path_id_various_emoji(self):
        # Test various types of emoji are properly handled
        # Simple emoji
        result = normalize_path_id("Music 🎵 Player")
        self.assertEqual(result, "Music_Player")

        # Emoji with skin tone modifier
        result = normalize_path_id("Developer 👨‍💻 Tools")
        self.assertEqual(result, "Developer_Tools")

        # Multiple emoji
        result = normalize_path_id("Fun 🎉🎊🎈 Party App")
        self.assertEqual(result, "Fun_Party_App")

        # Emoji at start and end
        result = normalize_path_id("🚀 Space Explorer 🌟")
        self.assertEqual(result, "Space_Explorer")

        # Flag emoji
        result = normalize_path_id("World 🇺🇸 Travel")
        self.assertEqual(result, "World_Travel")

        # Symbol emoji
        result = normalize_path_id("Check ✅ List ❌")
        self.assertEqual(result, "Check_List")

    def _test_platforms(self, input, testval):
        utils._sys_platform = input
        pf = _get_platform()
        self.assertTrue(pf == testval)
        # with patch('kivy.utils._sys_platform') as m:
        #     m.__str__.return_value = input
        #     m.__eq__ = lambda x, y: str(x) == y
        #     pf = _get_platform()
        #     self.assertTrue(str(pf) == testval)

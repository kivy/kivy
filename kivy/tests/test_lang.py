'''
Language tests
==============
'''

import unittest


class TestClass(object):
    obj = None


class LangTestCase(unittest.TestCase):

    def import_builder(self):
        from kivy.factory import Factory
        from kivy.lang import Builder
        Factory.register('TestClass', cls=TestClass)
        return Builder

    def test_loading_failed_1(self):
        # invalid indent
        Builder = self.import_builder()
        from kivy.lang import ParserError
        try:
            Builder.load_string('''#:kivy 1.0
            <TestClass>:
            ''')
            self.fail('Invalid indentation.')
        except ParserError:
            pass

    def test_parser_numeric_1(self):
        Builder = self.import_builder()
        Builder.load_string('<TestClass>:\n\tobj: (.5, .5, .5)')
        wid = TestClass()
        Builder.apply(wid)
        self.assertEqual(wid.obj, (0.5, 0.5, 0.5))

    def test_parser_numeric_2(self):
        Builder = self.import_builder()
        Builder.load_string('<TestClass>:\n\tobj: (0.5, 0.5, 0.5)')
        wid = TestClass()
        Builder.apply(wid)
        self.assertEqual(wid.obj, (0.5, 0.5, 0.5))



import unittest


class InvalidLangTestCase(unittest.TestCase):

    def test_invalid_childname(self):
        from kivy.lang import Builder, ParserException
        from kivy.factory import FactoryException
        try:
            Builder.load_string('''
Widget:
    FloatLayout:
        size: self.parent.size
        Button:
            text: "text"
            size_hint:(0.1, 0.1)
            pos_hint:{'x':0.45, 'y':0.45}
    thecursor.Cursor:
            ''')
            self.fail('Invalid children name')
        except ParserException:
            pass
        except FactoryException:
            pass

    def test_invalid_childname_before(self):
        from kivy.lang import Builder, ParserException
        try:
            Builder.load_string('''
Widget:
    thecursor.Cursor:
    FloatLayout:
        size: self.parent.size
        Button:
            text: "text"
            size_hint:(0.1, 0.1)
            pos_hint:{'x':0.45, 'y':0.45}
            ''')
            self.fail('Invalid children name')
        except ParserException:
            pass

'''
Language tests
==============
'''

import unittest
import os
from weakref import proxy
from functools import partial


class BaseClass(object):
    uid = 0

    # base class needed for builder
    def __init__(self, **kwargs):
        super(BaseClass, self).__init__()
        self.proxy_ref = proxy(self)
        self.children = []
        self.parent = None
        self.binded_func = {}
        self.id = None
        self.ids = {}
        self.cls = []
        self.ids = {}
        self.uid = BaseClass.uid
        BaseClass.uid += 1

    def add_widget(self, widget):
        self.children.append(widget)
        widget.parent = self

    def dispatch(self, event_type, *largs, **kwargs):
        pass

    def create_property(self, name, value=None, default_value=True):
        pass

    def is_event_type(self, key):
        return key.startswith('on_')

    def fbind(self, name, func, *largs):
        self.binded_func[name] = partial(func, *largs)
        return True

    def apply_class_lang_rules(
            self, root=None, ignored_consts=set(), rule_children=None):
        pass


class TLangClass(BaseClass):
    obj = None


class TLangClass2(BaseClass):
    obj = None


class TLangClass3(BaseClass):
    obj = None


class LangTestCase(unittest.TestCase):

    def import_builder(self):
        from kivy.factory import Factory
        from kivy.lang import BuilderBase
        Builder = BuilderBase()
        Factory.register('TLangClass', cls=TLangClass)
        Factory.register('TLangClass2', cls=TLangClass2)
        Factory.register('TLangClass3', cls=TLangClass3)
        return Builder

    def test_loading_failed_1(self):
        # invalid indent
        Builder = self.import_builder()
        from kivy.lang import ParserException
        try:
            Builder.load_string('''#:kivy 1.0
            <TLangClass>:
            ''')
            self.fail('Invalid indentation.')
        except ParserException:
            pass

    def test_parser_numeric_1(self):
        Builder = self.import_builder()
        Builder.load_string('<TLangClass>:\n\tobj: (.5, .5, .5)')
        wid = TLangClass()
        Builder.apply(wid)
        self.assertEqual(wid.obj, (0.5, 0.5, 0.5))

    def test_parser_numeric_2(self):
        Builder = self.import_builder()
        Builder.load_string('<TLangClass>:\n\tobj: (0.5, 0.5, 0.5)')
        wid = TLangClass()
        Builder.apply(wid)
        self.assertEqual(wid.obj, (0.5, 0.5, 0.5))

    def test_references(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TLangClass>:
    textinput: textinput
    TLangClass2:
        id: textinput
        ''')
        wid = TLangClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_references_with_template(self):
        Builder = self.import_builder()
        Builder.load_string('''
[Item@TLangClass3]:
    title: ctx.title
<TLangClass>:
    textinput: textinput
    Item:
        title: 'bleh'
    TLangClass2:
        id: textinput
        ''')
        wid = TLangClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_references_with_template_case_2(self):
        Builder = self.import_builder()
        Builder.load_string('''
[Item@TLangClass3]:
    title: ctx.title
<TLangClass>:
    textinput: textinput
    TLangClass2:
        id: textinput
        Item:
            title: 'bleh'
        ''')
        wid = TLangClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_references_with_template_case_3(self):
        Builder = self.import_builder()
        Builder.load_string('''
[Item@TLangClass3]:
    title: ctx.title
<TLangClass>:
    textinput: textinput
    TLangClass2:
        Item:
            title: 'bleh'
        TLangClass2:
            TLangClass2:
                id: textinput
        ''')
        wid = TLangClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_with_multiline(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TLangClass>:
    on_press:
        print('hello world')
        print('this is working !')
        self.a = 1
''')
        wid = TLangClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEqual(wid.a, 1)

    def test_with_eight_spaces(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TLangClass>:
        on_press:
                print('hello world')
                print('this is working !')
                self.a = 1
''')
        wid = TLangClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEqual(wid.a, 1)

    def test_with_one_space(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TLangClass>:
 on_press:
  print('hello world')
  print('this is working !')
  self.a = 1
''')
        wid = TLangClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEqual(wid.a, 1)

    def test_with_two_spaces(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TLangClass>:
  on_press:
    print('hello world')
    print('this is working !')
    self.a = 1
''')
        wid = TLangClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEqual(wid.a, 1)

    def test_property_trailingspace(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TLangClass>:
    text : 'original'
    on_press : self.text = 'changed'
''')
        wid = TLangClass()
        Builder.apply(wid)

        self.assertTrue('on_press' in wid.binded_func)
        self.assertEqual(wid.text, 'original')

        # call the on_press and check the result
        wid.binded_func['on_press']()
        self.assertEqual(wid.text, 'changed')

    def test_kv_python_init(self):
        from kivy.factory import Factory
        from kivy.lang import Builder
        from kivy.uix.widget import Widget

        class MyObject(object):
            value = 55

        class MyWidget(Widget):
            cheese = MyObject()

        Builder.load_string('''
<MyWidget>:
    x: 55
    y: self.width + 10
    height: self.cheese.value
    width: 44

<MySecondWidget@Widget>:
    x: 55
    Widget:
        x: 23
''')

        w = MyWidget(x=22, height=12, y=999)
        self.assertEqual(w.x, 22)
        self.assertEqual(w.width, 44)
        self.assertEqual(w.y, 44 + 10)
        self.assertEqual(w.height, 12)

        w2 = Factory.MySecondWidget(x=999)
        self.assertEqual(w2.x, 999)
        self.assertEqual(w2.children[0].x, 23)

    def test_apply_rules(self):
        Builder = self.import_builder()
        Builder.load_string('<TLangClassCustom>:\n\tobj: 42')
        wid = TLangClass()
        Builder.apply(wid)
        self.assertIsNone(wid.obj)
        Builder.apply_rules(wid, 'TLangClassCustom')
        self.assertEqual(wid.obj, 42)

    def test_load_utf8(self):
        from tempfile import mkstemp
        from kivy.lang import Builder
        fd, name = mkstemp()
        os.write(fd, '''

Label:
    text: 'é 😊'
'''.encode('utf8'))
        root = Builder.load_file(name)
        assert root.text == 'é 😊'
        os.close(fd)


if __name__ == '__main__':
    unittest.main()

'''
Language tests
==============
'''

import unittest
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

    def create_property(self, name, value=None):
        pass

    def is_event_type(self, key):
        return key.startswith('on_')

    def fbind(self, name, func, *largs):
        self.binded_func[name] = partial(func, *largs)
        return True


class TestClass(BaseClass):
    obj = None


class TestClass2(BaseClass):
    obj = None


class TestClass3(BaseClass):
    obj = None


class LangTestCase(unittest.TestCase):

    def import_builder(self):
        from kivy.factory import Factory
        from kivy.lang import BuilderBase
        Builder = BuilderBase()
        Factory.register('TestClass', cls=TestClass)
        Factory.register('TestClass2', cls=TestClass2)
        Factory.register('TestClass3', cls=TestClass3)
        return Builder

    def test_loading_failed_1(self):
        # invalid indent
        Builder = self.import_builder()
        from kivy.lang import ParserException
        try:
            Builder.load_string('''#:kivy 1.0
            <TestClass>:
            ''')
            self.fail('Invalid indentation.')
        except ParserException:
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

    def test_references(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TestClass>:
    textinput: textinput
    TestClass2:
        id: textinput
        ''')
        wid = TestClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_references_with_template(self):
        Builder = self.import_builder()
        Builder.load_string('''
[Item@TestClass3]:
    title: ctx.title
<TestClass>:
    textinput: textinput
    Item:
        title: 'bleh'
    TestClass2:
        id: textinput
        ''')
        wid = TestClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_references_with_template_case_2(self):
        Builder = self.import_builder()
        Builder.load_string('''
[Item@TestClass3]:
    title: ctx.title
<TestClass>:
    textinput: textinput
    TestClass2:
        id: textinput
        Item:
            title: 'bleh'
        ''')
        wid = TestClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_references_with_template_case_3(self):
        Builder = self.import_builder()
        Builder.load_string('''
[Item@TestClass3]:
    title: ctx.title
<TestClass>:
    textinput: textinput
    TestClass2:
        Item:
            title: 'bleh'
        TestClass2:
            TestClass2:
                id: textinput
        ''')
        wid = TestClass()
        Builder.apply(wid)

        self.assertTrue(hasattr(wid, 'textinput'))
        self.assertTrue(getattr(wid, 'textinput') is not None)

    def test_with_multiline(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TestClass>:
    on_press:
        print('hello world')
        print('this is working !')
        self.a = 1
''')
        wid = TestClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEquals(wid.a, 1)

    def test_with_eight_spaces(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TestClass>:
        on_press:
                print('hello world')
                print('this is working !')
                self.a = 1
''')
        wid = TestClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEquals(wid.a, 1)

    def test_with_one_space(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TestClass>:
 on_press:
  print('hello world')
  print('this is working !')
  self.a = 1
''')
        wid = TestClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEquals(wid.a, 1)

    def test_with_two_spaces(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TestClass>:
  on_press:
    print('hello world')
    print('this is working !')
    self.a = 1
''')
        wid = TestClass()
        Builder.apply(wid)
        wid.a = 0

        self.assertTrue('on_press' in wid.binded_func)
        wid.binded_func['on_press']()
        self.assertEquals(wid.a, 1)

    def test_property_trailingspace(self):
        Builder = self.import_builder()
        Builder.load_string('''
<TestClass>:
    text : 'original'
    on_press : self.text = 'changed'
''')
        wid = TestClass()
        Builder.apply(wid)

        self.assertTrue('on_press' in wid.binded_func)
        self.assertEquals(wid.text, 'original')

        # call the on_press and check the result
        wid.binded_func['on_press']()
        self.assertEquals(wid.text, 'changed')

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
        Builder.load_string('<TestClassCustom>:\n\tobj: 42')
        wid = TestClass()
        Builder.apply(wid)
        self.assertIsNone(wid.obj)
        Builder.apply_rules(wid, 'TestClassCustom')
        self.assertEqual(wid.obj, 42)


if __name__ == '__main__':
    unittest.main()

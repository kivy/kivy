import unittest

rules = '''
<CustomLabel>:
    title: 'invalid'
<TestWidget>:
    source: 'invalid.png'

<TestWidget2>:
    source: 'invalid.png'
    source3: 'valid.png'

[MItem@TestWidget2]:
    source: ctx.get('anotherctxvalue')

<MainWidget>:
    refwid: myref
    refwid2: myref2
    MItem:
        id: myref2
        anotherctxvalue: 'valid.png'
    TestWidget:
        canvas:
            Color:
                rgba: 1, 1, 1, 1
        id: myref
        source: 'valid.png'
        source2: 'valid.png'
        source3: self.source + 'from source3' if self.can_edit else 'valid.png'
        on_release: root.edit()
        CustomLabel:
            title: 'valid'
'''


class LangComplexTestCase(unittest.TestCase):

    def test_complex_rewrite(self):
        # this test cover a large part of the lang
        # and was used for testing the validity of the new rewrite lang
        # however, it's not self explained enough :/

        from kivy.lang import Builder
        from kivy.uix.widget import Widget
        from kivy.uix.label import Label
        from kivy.factory import Factory
        from kivy.properties import StringProperty, ObjectProperty, \
            BooleanProperty

        Builder.load_string(rules)

        class TestWidget(Widget):
            source = StringProperty('')
            source2 = StringProperty('')
            source3 = StringProperty('')
            can_edit = BooleanProperty(False)

            def __init__(self, **kwargs):
                self.register_event_type('on_release')
                super(TestWidget, self).__init__(**kwargs)

            def on_release(self):
                pass

        class MainWidget(Widget):
            refwid = ObjectProperty(None)
            refwid2 = ObjectProperty(None)

        class TestWidget2(Widget):
            pass

        class CustomLabel(Label):
            pass

        Factory.register('CustomLabel', cls=CustomLabel)
        Factory.register('TestWidget', cls=TestWidget)
        Factory.register('TestWidget2', cls=TestWidget2)

        a = MainWidget()
        self.assertTrue(isinstance(a.refwid, TestWidget))
        self.assertEquals(a.refwid.source, 'valid.png')
        self.assertEquals(a.refwid.source2, 'valid.png')
        self.assertEquals(a.refwid.source3, 'valid.png')
        self.assertTrue(len(a.refwid.children) == 1)
        self.assertEquals(a.refwid.children[0].title, 'valid')
        self.assertTrue(isinstance(a.refwid2, TestWidget2))
        self.assertEquals(a.refwid2.source, 'valid.png')

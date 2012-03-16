'''
Test properties attached to a widget
'''

import unittest


class Widget(object):
    '''Fake widget class'''

    def __init__(self, **kwargs):
        super(Widget, self).__init__(**kwargs)
        self.__dict__['__uid'] = 1
        self.__dict__['__storage'] = {}


wid = Widget()


class PropertiesTestCase(unittest.TestCase):

    def test_base(self):
        from kivy.properties import Property

        a = Property(-1)
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), -1)
        a.set(wid, 0)
        self.assertEqual(a.get(wid), 0)
        a.set(wid, 1)
        self.assertEqual(a.get(wid), 1)

    def test_observer(self):
        from kivy.properties import Property

        a = Property(-1)
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), -1)
        global observe_called
        observe_called = 0

        def observe(obj, value):
            global observe_called
            observe_called = 1
        a.bind(wid, observe)

        a.set(wid, 0)
        self.assertEqual(a.get(wid), 0)
        self.assertEqual(observe_called, 1)
        observe_called = 0
        a.set(wid, 0)
        self.assertEqual(a.get(wid), 0)
        self.assertEqual(observe_called, 0)
        a.set(wid, 1)
        self.assertEqual(a.get(wid), 1)
        self.assertEqual(observe_called, 1)

    def test_objectcheck(self):
        from kivy.properties import ObjectProperty

        a = ObjectProperty(False)
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), False)
        a.set(wid, True)
        self.assertEqual(a.get(wid), True)

    def test_stringcheck(self):
        from kivy.properties import StringProperty

        a = StringProperty('')
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), '')
        a.set(wid, 'hello')
        self.assertEqual(a.get(wid), 'hello')

        try:
            a.set(wid, 88) # number shouldn't be accepted
            self.fail('string accept number, fail.')
        except ValueError:
            pass

    def test_numericcheck(self):
        from kivy.properties import NumericProperty

        a = NumericProperty(0)
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), 0)
        a.set(wid, 99)
        self.assertEqual(a.get(wid), 99)

        try:
            a.set(wid, '') # string shouldn't be accepted
            self.fail('number accept string, fail.')
        except ValueError:
            pass

    def test_propertynone(self):
        from kivy.properties import NumericProperty

        a = NumericProperty(0, allownone=True)
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), 0)
        try:
            a.set(wid, None)
            self.assertEqual(a.get(wid), None)
        except ValueError:
            pass
        a.set(wid, 1)
        self.assertEqual(a.get(wid), 1)

    def test_alias(self):
        from kivy.properties import NumericProperty, AliasProperty

        wid.__class__.x = x = NumericProperty(0)
        x.link(wid, 'x')
        x.link_deps(wid, 'x')
        wid.__class__.width = width = NumericProperty(100)
        width.link(wid, 'width')
        width.link_deps(wid, 'width')

        def get_right(self):
            return x.get(self) + width.get(self)

        def set_right(self, value):
            x.set(self, value - width.get(self))

        right = AliasProperty(get_right, set_right, bind=('x', 'width'))
        right.link(wid, 'right')
        right.link_deps(wid, 'right')

        self.assertEqual(right.get(wid), 100)
        x.set(wid, 500)
        self.assertEqual(right.get(wid), 600)
        width.set(wid, 50)
        self.assertEqual(right.get(wid), 550)

        right.set(wid, 100)
        self.assertEqual(width.get(wid), 50)
        self.assertEqual(x.get(wid), 50)

        # test observer
        global observe_called
        observe_called = 0

        def observe(obj, value):
            global observe_called
            observe_called = 1
        right.bind(wid, observe)

        x.set(wid, 100)
        self.assertEqual(observe_called, 1)
        observe_called = 0

        x.set(wid, 100)
        self.assertEqual(observe_called, 0)

        width.set(wid, 900)
        self.assertEqual(observe_called, 1)
        observe_called = 0

        right.set(wid, 700)
        self.assertEqual(observe_called, 1)
        observe_called = 0

        right.set(wid, 700)
        self.assertEqual(observe_called, 0)

    def test_reference(self):
        from kivy.properties import NumericProperty, ReferenceListProperty

        x = NumericProperty(0)
        x.link(wid, 'x')
        x.link_deps(wid, 'x')
        y = NumericProperty(0)
        y.link(wid, 'y')
        y.link_deps(wid, 'y')
        pos = ReferenceListProperty(x, y)
        pos.link(wid, 'pos')
        pos.link_deps(wid, 'pos')

        self.assertEqual(x.get(wid), 0)
        self.assertEqual(y.get(wid), 0)
        self.assertEqual(pos.get(wid), [0, 0])

        x.set(wid, 50)
        self.assertEqual(pos.get(wid), [50, 0])

        y.set(wid, 50)
        self.assertEqual(pos.get(wid), [50, 50])

        pos.set(wid, [0, 0])
        self.assertEqual(pos.get(wid), [0, 0])
        self.assertEqual(x.get(wid), 0)
        self.assertEqual(y.get(wid), 0)

        # test observer
        global observe_called
        observe_called = 0

        def observe(obj, value):
            global observe_called
            observe_called = 1
        pos.bind(wid, observe)

        self.assertEqual(observe_called, 0)
        x.set(wid, 99)
        self.assertEqual(observe_called, 1)

    def test_dict(self):
        from kivy.properties import DictProperty

        x = DictProperty({})
        x.link(wid, 'x')
        x.link_deps(wid, 'x')

        # test observer
        global observe_called
        observe_called = 0

        def observe(obj, value):
            global observe_called
            observe_called = 1

        x.bind(wid, observe)

        observe_called = 0
        x.get(wid)['toto'] = 1
        self.assertEqual(observe_called, 1)

        observe_called = 0
        x.get(wid)['toto'] = 2
        self.assertEqual(observe_called, 1)

        observe_called = 0
        x.get(wid)['youupi'] = 2
        self.assertEqual(observe_called, 1)

        observe_called = 0
        del x.get(wid)['toto']
        self.assertEqual(observe_called, 1)

        observe_called = 0
        x.get(wid).update({'bleh': 5})
        self.assertEqual(observe_called, 1)


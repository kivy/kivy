'''
Test properties attached to a widget
'''

import unittest
from kivy.event import EventDispatcher
from functools import partial


class TestProperty(EventDispatcher):
    pass


wid = TestProperty()


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

        a = StringProperty()
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), '')
        a.set(wid, 'hello')
        self.assertEqual(a.get(wid), 'hello')

        try:
            a.set(wid, 88)  # number shouldn't be accepted
            self.fail('string accept number, fail.')
        except ValueError:
            pass

    def test_numericcheck(self):
        from kivy.properties import NumericProperty

        a = NumericProperty()
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), 0)
        a.set(wid, 99)
        self.assertEqual(a.get(wid), 99)

        #try:
        #    a.set(wid, '')  # string shouldn't be accepted
        #    self.fail('number accept string, fail.')
        #except ValueError:
        #    pass

    def test_listcheck(self):
        from kivy.properties import ListProperty

        a = ListProperty()
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), [])
        a.set(wid, [1, 2, 3])
        self.assertEqual(a.get(wid), [1, 2, 3])

    def test_dictcheck(self):
        from kivy.properties import DictProperty

        a = DictProperty()
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), {})
        a.set(wid, {'foo': 'bar'})
        self.assertEqual(a.get(wid), {'foo': 'bar'})

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

    def test_reference_child_update(self):
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

        pos.get(wid)[0] = 10
        self.assertEqual(pos.get(wid), [10, 0])

        pos.get(wid)[:] = (20, 30)
        self.assertEqual(pos.get(wid), [20, 30])

    def test_dict(self):
        from kivy.properties import DictProperty

        x = DictProperty()
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

    def test_aliasproperty_with_cache(self):
        from kivy.properties import NumericProperty, AliasProperty
        global observe_called
        observe_called = 0

        class CustomAlias(EventDispatcher):
            basevalue = NumericProperty(1)

            def _get_prop(self):
                global observe_called
                observe_called += 1
                return self.basevalue * 2

            def _set_prop(self, value):
                self.basevalue = value / 2

            prop = AliasProperty(_get_prop, _set_prop,
                    bind=('basevalue', ), cache=True)

        # initial checks
        wid = CustomAlias()
        self.assertEqual(observe_called, 0)
        self.assertEqual(wid.basevalue, 1)
        self.assertEqual(observe_called, 0)

        # first call, goes in cache
        self.assertEqual(wid.prop, 2)
        self.assertEqual(observe_called, 1)

        # second call, cache used
        self.assertEqual(wid.prop, 2)
        self.assertEqual(observe_called, 1)

        # change the base value, should trigger an update for the cache
        wid.basevalue = 4
        self.assertEqual(observe_called, 2)

        # now read the value again, should use the cache too
        self.assertEqual(wid.prop, 8)
        self.assertEqual(observe_called, 2)

        # change the prop itself, should trigger an update for the cache
        wid.prop = 4
        self.assertEqual(observe_called, 3)
        self.assertEqual(wid.basevalue, 2)
        self.assertEqual(wid.prop, 4)
        self.assertEqual(observe_called, 3)

    def test_bounded_numeric_property(self):
        from kivy.properties import BoundedNumericProperty

        bnp = BoundedNumericProperty(0.0, min=0.0, max=3.5)

        bnp.link(wid, 'bnp')

        bnp.set(wid, 1)
        bnp.set(wid, 0.0)
        bnp.set(wid, 3.1)
        bnp.set(wid, 3.5)
        self.assertRaises(ValueError, partial(bnp.set, wid, 3.6))
        self.assertRaises(ValueError, partial(bnp.set, wid, -3))

    def test_bounded_numeric_property_error_value(self):
        from kivy.properties import BoundedNumericProperty

        bnp = BoundedNumericProperty(0, min=-5, max=5, errorvalue=1)
        bnp.link(wid, 'bnp')

        bnp.set(wid, 1)
        self.assertEqual(bnp.get(wid), 1)

        bnp.set(wid, 5)
        self.assertEqual(bnp.get(wid), 5)

        bnp.set(wid, 6)
        self.assertEqual(bnp.get(wid), 1)

        bnp.set(wid, -5)
        self.assertEqual(bnp.get(wid), -5)

        bnp.set(wid, -6)
        self.assertEqual(bnp.get(wid), 1)

    def test_bounded_numeric_property_error_handler(self):
        from kivy.properties import BoundedNumericProperty

        bnp = BoundedNumericProperty(
            0, min=-5, max=5,
            errorhandler=lambda x: 5 if x > 5 else -5)

        bnp.link(wid, 'bnp')

        bnp.set(wid, 1)
        self.assertEqual(bnp.get(wid), 1)

        bnp.set(wid, 5)
        self.assertEqual(bnp.get(wid), 5)

        bnp.set(wid, 10)
        self.assertEqual(bnp.get(wid), 5)

        bnp.set(wid, -5)
        self.assertEqual(bnp.get(wid), -5)

        bnp.set(wid, -10)
        self.assertEqual(bnp.get(wid), -5)

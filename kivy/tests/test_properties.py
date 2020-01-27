'''
Test properties attached to a widget
'''

import unittest
from kivy.event import EventDispatcher
from functools import partial


class _TestProperty(EventDispatcher):
    pass


wid = _TestProperty()


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

        # try:
        #    a.set(wid, '')  # string shouldn't be accepted
        #    self.fail('number accept string, fail.')
        # except ValueError:
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

    def test_numeric_string_with_units_check(self):
        from kivy.properties import NumericProperty

        a = NumericProperty()
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), 0)

        a.set(wid, '55dp')
        from kivy.core.window import Window
        density = Window._density if hasattr(Window, '_density') else 1
        self.assertEqual(a.get(wid), 55 * density)
        self.assertEqual(a.get_format(wid), 'dp')

        a.set(wid, u'55dp')
        self.assertEqual(a.get(wid), 55 * density)
        self.assertEqual(a.get_format(wid), 'dp')

        a.set(wid, '99in')
        self.assertEqual(a.get(wid), 9504.0 * density)
        self.assertEqual(a.get_format(wid), 'in')

        a.set(wid, u'99in')
        self.assertEqual(a.get(wid), 9504.0 * density)
        self.assertEqual(a.get_format(wid), 'in')

    def test_numeric_string_without_units(self):
        from kivy.properties import NumericProperty

        a = NumericProperty()
        a.link(wid, 'a')
        a.link_deps(wid, 'a')
        self.assertEqual(a.get(wid), 0)

        a.set(wid, '2')
        self.assertEqual(a.get(wid), 2)

    def test_property_rebind(self):
        from kivy.uix.label import Label
        from kivy.uix.togglebutton import ToggleButton
        from kivy.lang import Builder
        from kivy.properties import ObjectProperty, DictProperty, AliasProperty
        from kivy.clock import Clock

        class ObjWidget(Label):
            button = ObjectProperty(None, rebind=True, allownone=True)

        class ObjWidgetRebindFalse(Label):
            button = ObjectProperty(None, rebind=False, allownone=True)

        class DictWidget(Label):
            button = DictProperty({'button': None}, rebind=True,
                                  allownone=True)

        class DictWidgetFalse(Label):
            button = DictProperty({'button': None}, rebind=False)

        class AliasWidget(Label):
            _button = None

            def setter(self, value):
                self._button = value
                return True

            def getter(self):
                return self._button
            button = AliasProperty(getter, setter, rebind=True)

        Builder.load_string('''
<ObjWidget>:
    text: self.button.state if self.button is not None else 'Unset'

<ObjWidgetRebindFalse>:
    text: self.button.state if self.button is not None else 'Unset'

<AliasWidget>:
    text: self.button.state if self.button is not None else 'Unset'

<DictWidget>:
    text: self.button.button.state if self.button.button is not None\
    else 'Unset'

<DictWidgetFalse>:
    text: self.button.button.state if self.button.button is not None\
    else 'Unset'
        ''')

        obj = ObjWidget()
        obj_false = ObjWidgetRebindFalse()
        dict_rebind = DictWidget()
        dict_false = DictWidgetFalse()
        alias_rebind = AliasWidget()
        button = ToggleButton()
        Clock.tick()
        self.assertEqual(obj.text, 'Unset')
        self.assertEqual(obj_false.text, 'Unset')
        self.assertEqual(dict_rebind.text, 'Unset')
        self.assertEqual(dict_false.text, 'Unset')
        self.assertEqual(alias_rebind.text, 'Unset')

        obj.button = button
        obj_false.button = button
        dict_rebind.button.button = button
        dict_false.button.button = button
        alias_rebind.button = button
        Clock.tick()
        self.assertEqual(obj.text, 'normal')
        self.assertEqual(obj_false.text, 'normal')
        self.assertEqual(dict_rebind.text, 'normal')
        self.assertEqual(dict_false.text, 'Unset')
        self.assertEqual(alias_rebind.text, 'normal')

        button.state = 'down'
        Clock.tick()
        self.assertEqual(obj.text, 'down')
        self.assertEqual(obj_false.text, 'normal')
        self.assertEqual(dict_rebind.text, 'down')
        self.assertEqual(dict_false.text, 'Unset')
        self.assertEqual(alias_rebind.text, 'down')

        button.state = 'normal'
        Clock.tick()
        self.assertEqual(obj.text, 'normal')
        self.assertEqual(obj_false.text, 'normal')
        self.assertEqual(dict_rebind.text, 'normal')
        self.assertEqual(dict_false.text, 'Unset')
        self.assertEqual(alias_rebind.text, 'normal')

        obj.button = None
        obj_false.button = None
        dict_rebind.button.button = None
        dict_false.button.button = None
        alias_rebind.button = None
        Clock.tick()
        self.assertEqual(obj.text, 'Unset')
        self.assertEqual(obj_false.text, 'Unset')
        self.assertEqual(dict_rebind.text, 'Unset')
        self.assertEqual(dict_false.text, 'Unset')
        self.assertEqual(alias_rebind.text, 'Unset')

    def test_color_property(self):
        from kivy.properties import ColorProperty

        color = ColorProperty()
        color.link(wid, 'color')
        color.link_deps(wid, 'color')
        self.assertEqual(color.get(wid), [1, 1, 1, 1])

        color.set(wid, "#00ff00")
        self.assertEqual(color.get(wid), [0, 1, 0, 1])

        color.set(wid, "#7f7fff7f")
        self.assertEqual(color.get(wid)[0], 127 / 255.)
        self.assertEqual(color.get(wid)[1], 127 / 255.)
        self.assertEqual(color.get(wid)[2], 1)
        self.assertEqual(color.get(wid)[3], 127 / 255.)

        color.set(wid, (1, 1, 0))
        self.assertEqual(color.get(wid), [1, 1, 0, 1])
        color.set(wid, (1, 1, 0, 0))
        self.assertEqual(color.get(wid), [1, 1, 0, 0])

    def test_alias_property_without_setter(self):
        from kivy.properties import AliasProperty

        expected_value = 5

        class CustomAlias(EventDispatcher):

            def _get_prop(self):
                self.getter_called += 1
                return expected_value

            prop = AliasProperty(_get_prop, None)

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.getter_called = 0

        # Initial checks
        wid = CustomAlias()
        self.assertEqual(wid.getter_called, 0)

        # Get value, should call getter once
        value = wid.prop
        self.assertEqual(value, expected_value)
        self.assertEqual(wid.getter_called, 1)

        # Setter should raise an AttributeError
        self.assertRaises(AttributeError, partial(setattr, wid, 'prop', 1))

    def test_alias_property(self):
        from kivy.properties import AliasProperty

        class CustomAlias(EventDispatcher):

            def _get_prop(self):
                self.getter_called += 1

            def _set_prop(self, value):
                self.setter_called += 1

            prop = AliasProperty(_get_prop, _set_prop)

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.getter_called = 0
                self.setter_called = 0
                self.callback_called = 0

        def callback(widget, value):
            widget.callback_called += 1

        # Initial checks
        wid = CustomAlias()
        wid.bind(prop=callback)
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.setter_called, 0)
        self.assertEqual(wid.callback_called, 0)

        # Set property, should call setter to set the value
        # Getter and callback should not be called because `_set_prop` doesn't
        # returns True
        wid.prop = 1
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.setter_called, 1)
        self.assertEqual(wid.callback_called, 0)

        # Set property to same value as before, should only call setter
        wid.prop = 1
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.setter_called, 2)
        self.assertEqual(wid.callback_called, 0)

        # Get value of the property, should call getter once
        self.assertEqual(wid.prop, None)
        self.assertEqual(wid.getter_called, 1)
        self.assertEqual(wid.setter_called, 2)
        self.assertEqual(wid.callback_called, 0)

    def test_alias_property_cache_true(self):
        from kivy.properties import AliasProperty

        expected_value = 5

        class CustomAlias(EventDispatcher):

            def _get_prop(self):
                self.getter_called += 1
                return expected_value

            def _set_prop(self, value):
                self.setter_called += 1
                return True

            prop = AliasProperty(_get_prop, _set_prop, cache=True)

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.getter_called = 0
                self.setter_called = 0

        # Initial checks
        wid = CustomAlias()
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.setter_called, 0)

        # Get value of the property, should call getter once
        value = wid.prop
        self.assertEqual(value, expected_value)
        self.assertEqual(wid.getter_called, 1)
        self.assertEqual(wid.setter_called, 0)

        # Get value of the property, should return cached value
        # Getter should not be called
        value = wid.prop
        self.assertEqual(value, expected_value)
        self.assertEqual(wid.getter_called, 1)
        self.assertEqual(wid.setter_called, 0)

        # Set value of property, should call getter and setter
        wid.prop = 10
        value = wid.prop
        self.assertEqual(value, expected_value)
        self.assertEqual(wid.setter_called, 1)
        self.assertEqual(wid.getter_called, 2)

    def test_alias_property_with_bind(self):
        from kivy.properties import NumericProperty, AliasProperty

        class CustomAlias(EventDispatcher):

            x = NumericProperty(0)
            width = NumericProperty(100)

            def get_right(self):
                return self.x + self.width

            def set_right(self, value):
                self.x = value - self.width

            right = AliasProperty(get_right, set_right, bind=('x', 'width'))

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.callback_called = 0

        # Assert values when setting x, width or right properties
        wid = CustomAlias()
        self.assertEqual(wid.right, 100)
        wid.x = 500
        self.assertEqual(wid.right, 600)
        wid.width = 50
        self.assertEqual(wid.right, 550)
        wid.right = 100
        self.assertEqual(wid.width, 50)
        self.assertEqual(wid.x, 50)

        def callback(widget, value):
            widget.callback_called += 1

        wid.bind(right=callback)

        # Callback should be called only when property changes
        wid.x = 100
        self.assertEqual(wid.callback_called, 1)
        wid.x = 100
        self.assertEqual(wid.callback_called, 1)
        wid.width = 900
        self.assertEqual(wid.callback_called, 2)
        wid.right = 700
        self.assertEqual(wid.callback_called, 3)
        wid.right = 700
        self.assertEqual(wid.callback_called, 3)

    def test_alias_property_with_force_dispatch_true(self):
        from kivy.properties import AliasProperty

        class CustomAlias(EventDispatcher):

            def _get_prop(self):
                self.getter_called += 1

            def _set_prop(self, value):
                self.setter_called += 1

            prop = AliasProperty(_get_prop, _set_prop, force_dispatch=True)

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.getter_called = 0
                self.setter_called = 0
                self.callback_called = 0

        def callback(widget, value):
            widget.callback_called += 1

        # Initial checks
        wid = CustomAlias()
        wid.bind(prop=callback)
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.setter_called, 0)
        self.assertEqual(wid.callback_called, 0)

        # Set property, should call setter to set the value and getter to
        # to get the value for dispatch call
        wid.prop = 1
        self.assertEqual(wid.getter_called, 1)
        self.assertEqual(wid.setter_called, 1)
        self.assertEqual(wid.callback_called, 1)

        # Set property to same value as before, setter and getter and callback
        # are called
        wid.prop = 1
        self.assertEqual(wid.getter_called, 2)
        self.assertEqual(wid.setter_called, 2)
        self.assertEqual(wid.callback_called, 2)

    def test_alias_property_cache_true_with_bind(self):
        from kivy.properties import NumericProperty, AliasProperty

        class CustomAlias(EventDispatcher):

            base_value = NumericProperty(1)

            def _get_prop(self):
                self.getter_called += 1
                return self.base_value * 2

            def _set_prop(self, value):
                self.base_value = value / 2

            prop = AliasProperty(_get_prop, _set_prop,
                                 bind=('base_value',),
                                 cache=True)

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.getter_called = 0

        # Initial checks
        wid = CustomAlias()
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.base_value, 1)
        self.assertEqual(wid.getter_called, 0)

        # Change the base value, should trigger an update for the cache
        wid.base_value = 4
        self.assertEqual(wid.getter_called, 1)

        # Now read the value again, should use the cache
        self.assertEqual(wid.prop, 8)
        self.assertEqual(wid.getter_called, 1)

        # Change the prop itself, should trigger an update for the cache
        wid.prop = 4
        self.assertEqual(wid.getter_called, 2)
        self.assertEqual(wid.base_value, 2)
        self.assertEqual(wid.prop, 4)
        self.assertEqual(wid.getter_called, 2)

    def test_alias_property_cache_true_force_dispatch_true(self):
        from kivy.properties import AliasProperty

        class CustomAlias(EventDispatcher):

            def _get_prop(self):
                self.getter_called += 1
                return self.base_value * 2

            def _set_prop(self, value):
                self.setter_called += 1
                self.base_value = value / 2
                return True

            prop = AliasProperty(_get_prop, _set_prop,
                                 cache=True,
                                 force_dispatch=True)

            def __init__(self, **kwargs):
                super(CustomAlias, self).__init__(**kwargs)
                self.base_value = 1
                self.getter_called = 0
                self.setter_called = 0
                self.callback_called = 0

        def callback(widget, value):
            widget.callback_called += 1

        wid = CustomAlias()
        wid.bind(prop=callback)

        # Initial checks
        self.assertEqual(wid.base_value, 1)
        self.assertEqual(wid.getter_called, 0)
        self.assertEqual(wid.setter_called, 0)
        self.assertEqual(wid.callback_called, 0)

        # Set alias property some value, should call setter and then getter to
        # pass the value to callback
        wid.prop = 16
        self.assertEqual(wid.base_value, 8)
        self.assertEqual(wid.getter_called, 1)
        self.assertEqual(wid.setter_called, 1)
        self.assertEqual(wid.callback_called, 1)

        # Same as the step above, should call setter, getter and callback
        wid.prop = 16
        self.assertEqual(wid.base_value, 8)
        self.assertEqual(wid.getter_called, 2)
        self.assertEqual(wid.setter_called, 2)
        self.assertEqual(wid.callback_called, 2)

        # Get the value of property, should use cached value
        value = wid.prop
        self.assertEqual(value, 16)
        self.assertEqual(wid.getter_called, 2)
        self.assertEqual(wid.setter_called, 2)
        self.assertEqual(wid.callback_called, 2)


def test_dictproperty_is_none():
    from kivy.properties import DictProperty

    d1 = DictProperty(None)
    d1.link(wid, 'd1')
    assert d1.get(wid) is None

    d2 = DictProperty({'a': 1, 'b': 2}, allownone=True)
    d2.link(wid, 'd2')
    d2.set(wid, None)
    assert d2.get(wid) is None


def test_listproperty_is_none():
    from kivy.properties import ListProperty

    l1 = ListProperty(None)
    l1.link(wid, 'l1')
    assert l1.get(wid) is None

    l2 = ListProperty([1, 2, 3], allownone=True)
    l2.link(wid, 'l2')
    l2.set(wid, None)
    assert l2.get(wid) is None

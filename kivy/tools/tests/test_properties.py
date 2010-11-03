'''
New properties
'''

from init import test, import_kivy_no_window

# Fake widget class
class Widget(object):
    def __init__(self, **kwargs):
        super(Widget, self).__init__(**kwargs)
        self.__dict__['__uid'] = 1
wid = Widget()

def unittest_property():
    import_kivy_no_window()
    from kivy.c_ext.properties import Property

    a = Property(-1)
    a.link(wid, 'a')
    a.link_deps(wid, 'a')
    test(a.get(wid) == -1)
    a.set(wid, 0)
    test(a.get(wid) == 0)
    a.set(wid, 1)
    test(a.get(wid) == 1)

def unittest_property_observer():
    import_kivy_no_window()
    from kivy.c_ext.properties import Property

    a = Property(-1)
    a.link(wid, 'a')
    a.link_deps(wid, 'a')
    test(a.get(wid) == -1)
    global observe_called
    observe_called = 0
    def observe(obj, value):
        global observe_called
        observe_called = 1
    a.bind(wid, observe)

    a.set(wid, 0)
    test(a.get(wid) == 0)
    test(observe_called == 1)
    observe_called = 0
    a.set(wid, 0)
    test(a.get(wid) == 0)
    test(observe_called == 0)
    a.set(wid, 1)
    test(a.get(wid) == 1)
    test(observe_called == 1)

def unittest_property_stringcheck():
    import_kivy_no_window()
    from kivy.c_ext.properties import StringProperty

    a = StringProperty('')
    a.link(wid, 'a')
    a.link_deps(wid, 'a')
    test(a.get(wid) == '')
    a.set(wid, 'hello')
    test(a.get(wid) == 'hello')

    try:
        a.set(wid, 88) # number shouldn't be accepted
        test('string accept number, fail.' == 0)
    except ValueError:
        test('string dont accept number')

def unittest_property_numericcheck():
    import_kivy_no_window()
    from kivy.c_ext.properties import NumericProperty

    a = NumericProperty(0)
    a.link(wid, 'a')
    a.link_deps(wid, 'a')
    test(a.get(wid) == 0)
    a.set(wid, 99)
    test(a.get(wid) == 99)

    try:
        a.set(wid, '') # string shouldn't be accepted
        test('number accept string, fail.' == 0)
    except ValueError:
        test('number dont accept string')

def unittest_property_propertynone():
    import_kivy_no_window()
    from kivy.c_ext.properties import NumericProperty

    a = NumericProperty(0, allownone=True)
    a.link(wid, 'a')
    a.link_deps(wid, 'a')
    test(a.get(wid) == 0)
    try:
        a.set(wid, None)
        test(a.get(wid) == None)
    except ValueError, e:
        print e
        test('none not accepted' == 0)
    a.set(wid, 1)
    test(a.get(wid) == 1)

def unittest_property_alias():
    import_kivy_no_window()
    from kivy.c_ext.properties import NumericProperty, AliasProperty

    x = NumericProperty(0)
    x.link(wid, 'x')
    x.link_deps(wid, 'x')
    width = NumericProperty(100)
    width.link(wid, 'width')
    width.link_deps(wid, 'width')

    def get_right(self):
        return x.get(self) + width.get(self)
    def set_right(self, value):
        x.set(self, value - width.get(self))
    right = AliasProperty(get_right, set_right, bind=(x, width))
    right.link(wid, 'right')
    right.link_deps(wid, 'right')

    test(right.get(wid) == 100)
    x.set(wid, 500)
    test(right.get(wid) == 600)
    width.set(wid, 50)
    test(right.get(wid) == 550)

    right.set(wid, 100)
    test(width.get(wid) == 50)
    test(x.get(wid) == 50)

    # test observer
    global observe_called
    observe_called = 0
    def observe(obj, value):
        global observe_called
        observe_called = 1
    right.bind(wid, observe)

    x.set(wid, 100)
    test(observe_called == 1)
    observe_called = 0

    x.set(wid, 100)
    test(observe_called == 0)

    width.set(wid, 900)
    test(observe_called == 1)
    observe_called = 0

    right.set(wid, 700)
    test(observe_called == 1)
    observe_called = 0

    right.set(wid, 700)
    test(observe_called == 0)


def unittest_property_reference():
    import_kivy_no_window()
    from kivy.c_ext.properties import NumericProperty, ReferenceListProperty

    x = NumericProperty(0)
    x.link(wid, 'x')
    x.link_deps(wid, 'x')
    y = NumericProperty(0)
    y.link(wid, 'y')
    y.link_deps(wid, 'y')
    pos = ReferenceListProperty(x, y)
    pos.link(wid, 'pos')
    pos.link_deps(wid, 'pos')

    test(x.get(wid) == 0)
    test(y.get(wid) == 0)
    test(pos.get(wid) == [0, 0])

    x.set(wid, 50)
    test(pos.get(wid) == [50, 0])

    y.set(wid, 50)
    test(pos.get(wid) == [50, 50])

    pos.set(wid, [0, 0])
    test(pos.get(wid) == [0, 0])
    test(x.get(wid) == 0)
    test(y.get(wid) == 0)

    # test observer
    global observe_called
    observe_called = 0
    def observe(obj, value):
        global observe_called
        observe_called = 1
    pos.bind(wid, observe)

    test(observe_called == 0)
    x.set(wid, 99)
    test(observe_called == 1)


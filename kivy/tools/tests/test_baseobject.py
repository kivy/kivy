'''
BaseObject
'''

from init import test, import_kivy_no_window

def unittest_defaults():
    import_kivy_no_window()
    from kivy import BaseObject
    a = BaseObject()
    test(a.x == 0)
    test(a.y == 0)
    test(a.width == 0)
    test(a.height == 0)
    test(a.pos == (0, 0))
    test(a.size == (0, 0))

    # test every accessor
    a.x = 2
    test(a.x == 2)
    test(a.pos == (2, 0))
    test(a.center == (2, 0))

    a.y = 2
    test(a.y == 2)
    test(a.pos == (2, 2))
    test(a.center == (2, 2))

    a.pos = (0, 0)
    test(a.x == 0)
    test(a.y == 0)
    test(a.pos == (0, 0))
    test(a.center == (0, 0))

    a.width = 2
    test(a.width == 2)
    test(a.size == (2, 0))
    test(a.center == (1, 0))

    a.height = 2
    test(a.height == 2)
    test(a.size == (2, 2))
    test(a.center == (1, 1))

    a.size = (0, 0)
    test(a.width == 0)
    test(a.height == 0)
    test(a.size == (0, 0))
    test(a.center == (0, 0))

    a.center = (5, 5)
    test(a.x == 5)
    test(a.y == 5)
    test(a.pos == (5, 5))
    test(a.width == 0)
    test(a.height == 0)
    test(a.size == (0, 0))

    a.size = (20, 20)
    test(a.center == (15, 15))



from init import test, import_kivy_no_window

def unittest_basics():
    import_kivy_no_window()
    from kivy import Vector
    v = Vector(10, 10)
    test(v.x == 10)
    test(v.y == 10)

    a = Vector(1, 1)
    b = Vector(2, 2)

    test(a != b)

    # add
    c = a + b
    test(c.x == 3)
    test(c.y == 3)
    test(c[0] == 3)
    test(c[1] == 3)

    # sub
    c = a - b
    test(c.x == -1)
    test(c.y == -1)

    # mul
    c = b * 2
    test(c.x == 4)
    test(c.y == 4)

    # add with tuple
    c = b + (5, 6)
    test(c.x == 7)
    test(c.y == 8)

    # add with list
    c = b + [5, 6]
    test(c.x == 7)
    test(c.y == 8)

def unittest_methods():
    import_kivy_no_window()
    from kivy import Vector

    a = Vector(0, 10)
    test(a.length() == 10)

    b = Vector(0, 20)
    test(b.distance(a) == 10)


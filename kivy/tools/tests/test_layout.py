'''
Layout
'''

from init import test, import_kivy_no_window

def unittest_boxlayout_horizontal():
    _test_boxlayout('horizontal')

def unittest_boxlayout_vertical():
    _test_boxlayout('vertical')

def _test_boxlayout(orientation):
    import_kivy_no_window()
    from kivy import MTBoxLayout, MTWidget

    # note: this test act always if orientation
    # is a horizontal one. use sw() around pos or size
    # to ensure that the swap is done.

    def sw(tpl):
        tpl = tuple(map(int, tpl))
        if orientation == 'vertical':
            return tpl[1], tpl[0]
        return tpl


    # note: default spacing is 1
    # default padding is 0

    # default add
    m = MTBoxLayout(orientation=orientation)
    for x in xrange(10):
        m.add_widget(MTWidget(size=(10,10)))
    test(sw(m.size) == (109, 10))

    #
    # spacing to 10
    #
    m = MTBoxLayout(orientation=orientation, spacing=10)
    for x in xrange(10):
        m.add_widget(MTWidget(size=(10,10)))
    test(sw(m.size) == (190, 10))

    #
    # padding to 10
    #
    m = MTBoxLayout(orientation=orientation, padding=10, spacing=0)
    for x in xrange(10):
        m.add_widget(MTWidget(size=(10,10)))
    m.do_layout()

    # size should be 10 (number of widget) * width (10) + 2 * padding
    test(sw(m.size) == (120, 30))
    for x in xrange(10):
        if orientation == 'vertical':
            test(sw(m.children[x].pos) == (10 + x * 10, 10))
        else:
            test(sw(m.children[x].pos) == (10 + (9 - x) * 10, 10))


    #
    # testing size_hint with padding
    #
    m = MTBoxLayout(orientation=orientation, padding=10, spacing=0,
                    size_hint=(None, None), size=(500, 500))
    m.add_widget(MTWidget(size_hint=(1, 1)))
    m.do_layout()
    test(sw(m.size) == (500, 500))
    test(sw(m.children[0].size) == (480, 480))

    #
    # testing size_hint with spacing
    #
    m = MTBoxLayout(orientation=orientation, spacing=10,
                    size_hint=(None, None), size=(500, 500))
    m.add_widget(MTWidget(size_hint=(1, 1)))
    m.do_layout()

    # only one should have no impact
    test(sw(m.size) == (500, 500))
    test(sw(m.children[0].size) == (500, 500))

    # add a second widget
    m.add_widget(MTWidget(size_hint=(1, 1)))
    m.do_layout()

    # now, we should see difference
    test(sw(m.size) == (500, 500))
    test(sw(m.children[0].size) == (245, 500))
    test(sw(m.children[1].size) == (245, 500))


    #
    # testing with padding + spacing
    #
    m = MTBoxLayout(orientation=orientation, spacing=10, padding=10)
    for x in xrange(10):
        m.add_widget(MTWidget(size=(10,10)))
    m.do_layout()

    test(sw(m.size) == (210, 30))
    for x in xrange(10):
        if orientation == 'vertical':
            test(sw(m.children[x].pos) == (10 + x * 20, 10))
        else:
            test(sw(m.children[x].pos) == (10 + (9 - x) * 20, 10))


    #
    # testing with padding + spacing + size_hint
    #
    m = MTBoxLayout(orientation=orientation, spacing=10, padding=10,
                    size_hint=(None, None), size=(500, 500))
    m.add_widget(MTWidget(size_hint=(1, 1)))
    m.add_widget(MTWidget(size_hint=(1, 1)))
    m.do_layout()

    # now, we should see difference
    test(sw(m.size) == (500, 500))
    test(sw(m.children[0].size) == (235, 480))
    test(sw(m.children[1].size) == (235, 480))
    if orientation == 'vertical':
        test(sw(m.children[0].pos) == (10, 10))
        test(sw(m.children[1].pos) == (255, 10))
    else:
        test(sw(m.children[0].pos) == (255, 10))
        test(sw(m.children[1].pos) == (10, 10))


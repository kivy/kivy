'''
Widgets
'''

from init import test, import_kivy_no_window

def unittest_defaults():
    import_kivy_no_window()
    from kivy import MTWidget
    w = MTWidget()
    test(w.x == 0)
    test(w.y == 0)
    test(w.width == 100)
    test(w.height == 100)
    test(w.visible == True)
    test(w.draw_children == True)
    test(w.cls == '')

def unittest_visible_methods():
    import_kivy_no_window()
    from kivy import MTWidget
    w = MTWidget()
    w.hide()
    test(w.visible == False)
    w.show()
    test(w.visible == True)

def unittest_visible_events():
    import_kivy_no_window()
    from kivy import MTWidget

    global on_update_called
    on_update_called = 0

    def on_update():
        global on_update_called
        on_update_called += 1

    # by default, visible is True
    w = MTWidget()
    w.connect('on_draw', on_draw)
    w.dispatch_event('on_draw')
    test(on_draw_called == 1)

    # make it invisible
    w.visible = False
    w.dispatch_event('on_draw')
    test(on_draw_called == 1)

    # make it visible
    w.visible = True
    w.dispatch_event('on_draw')
    test(on_draw_called == 2)

    # create a new widget, visible default to False
    on_draw_called = 0
    w = MTWidget(visible=False)
    try:
        # XXX FIXME unable to connect to default on_draw
        # since it's not yet register.
        w.connect('on_draw', on_draw)
    except:
        pass
    w.dispatch_event('on_draw')
    test(on_draw_called == 0)

    w.visible = True
    w.connect('on_draw', on_draw)
    w.dispatch_event('on_draw')
    test(on_draw_called == 1)

def unittest_coordinate_transform():
    import_kivy_no_window()
    from kivy import MTWidget

    # child 2 inside child 1 inside child0
    child0 = MTWidget(pos=(100, 100))
    child1 = MTWidget(pos=(200, 200))
    child2 = MTWidget(pos=(300, 300))

    child0.add_widget(child1)
    child1.add_widget(child2)

    test(child0.pos == (100, 100))
    test(child1.pos == (200, 200))
    test(child2.pos == (300, 300))

    # screen coordinate is default
    test(child0.to_local(*child1.pos) == (200, 200))

    # using the relative attribute,
    # we should have relative coordinate
    test(child0.to_local(*child1.pos, relative=True) == (100, 100))
    test(child1.to_local(*child2.pos, relative=True) == (100, 100))

    # screen coordinate 400,400 is 100,100 in relative coordinate from child2
    test(child2.to_widget(400, 400, relative=True) == (100, 100))

    # 100, 100 relative coordinate from child2 is 400, 400 in screen coordinate
    test(child2.to_window(100, 100, relative=True) == (400, 400))


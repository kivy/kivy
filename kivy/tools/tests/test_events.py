'''
Events
'''

from init import test, import_kivy_no_window

def unittest_dispatcher():
    import_kivy_no_window()
    from kivy import EventDispatcher

    class MyEventDispatcher(EventDispatcher):
        def on_test(self, *largs):
            pass

    global testpass, testargs
    testpass = False
    testargs = None

    def callbacktest(*largs):
        global testpass, testargs
        testpass = True
        testargs = largs

    def resettest():
        global testpass, testargs
        testpass = False
        testargs = None

    a = MyEventDispatcher()

    # test unknown event
    resettest()
    try:
        a.connect('on_test', callbacktest)
    except:
        testpass = True

    test('no register' and testpass)

    # register event + test
    resettest()
    a.register_event_type('on_test')
    try:
        a.connect('on_test', callbacktest)
        testpass = True
    except:
        pass

    test('register' and testpass)

    # test dispatch
    resettest()
    a.dispatch_event('on_test')
    test('dispatch' and testpass)
    test(testargs == ())

    resettest()
    a.dispatch_event('on_test', 123)
    test('disp+arg' and testpass)
    test(testargs == (123,))

    resettest()
    a.dispatch_event('on_test', 123, 'blhe')
    test('disp+2args' and testpass)
    test(testargs == (123, 'blhe'))

    # remove handler
    resettest()
    a.remove_handler('on_test', callbacktest)
    a.dispatch_event('on_test')
    test('nohandler' and not testpass)



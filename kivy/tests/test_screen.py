
def test_switch_to():
    import kivy.uix.screenmanager as sm
    manager = sm.ScreenManager()
    screen1 = sm.Screen(name='first')
    screen2 = sm.Screen(name='second')
    manager.switch_to(screen1)
    manager.switch_to(screen2)
    manager.switch_to(screen1)
    manager.switch_to(screen2)
    manager.current = 'first'
    manager.switch_to(screen1)
    manager.current = 'second'
    manager.switch_to(screen2)

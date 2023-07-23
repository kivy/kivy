import pytest
import unittest
import kivy.uix.screenmanager as sm

transition_cls_names = (
    'ShaderTransition', 'SlideTransition', 'SwapTransition', 'FadeTransition',
    'WipeTransition', 'FallOutTransition', 'RiseInTransition', 'NoTransition',
    'CardTransition',
)

class ScreenManagerTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_switch_to():
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

    def test_switch_to_repeated_name_screen():
        manager = sm.ScreenManager()
        screen1 = sm.Screen(name='screen1')
        screen2 = sm.Screen(name='screen1')
        manager.add_widget(screen1)
        manager.add_widget(screen2)
        manager.switch_to(screen2)

    @pytest.mark.parametrize('transition_cls_name', transition_cls_names)
    def test_switching_does_not_affect_a_list_of_screens(transition_cls_name):
        transition_cls = getattr(sm, transition_cls_name)
        scrmgr = sm.ScreenManager()
        for i in range(3):
            scrmgr.add_widget(sm.Screen(name=str(i)))
        names = list(scrmgr.screen_names)
        scrmgr.transition = transition_cls()
        scrmgr.current = '1'
        assert names == scrmgr.screen_names
        scrmgr.transition = transition_cls()
        scrmgr.current = '2'
        assert names == scrmgr.screen_names

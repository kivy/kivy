import unittest
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.sandbox import Sandbox
from kivy.uix.button import Button
from kivy.base import runTouchApp
from kivy.tests.common import GraphicUnitTest
from kivy.lang import Builder
from kivy.input.motionevent import MotionEvent
from kivy.input.providers.mouse import MouseMotionEventProvider

class SandboxTest(unittest.TestCase):
    def setUp(self):
        self.root = Sandbox()

    #def test_start_app_with_sandbox(self):
        with self.root:
            Builder.load_string('''
<Button>:
    canvas:
        Color:
            rgb: (.3, .2, 0) if self.state == 'normal' else (.7, .7, 0)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgb: 1, 1, 1
        Rectangle:
            size: self.texture_size
            pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.
            texture: self.texture
    
    on_touch_up: root.d()
    on_touch_down: root.f()
    on_release: root.args()
    on_press: root.args()
''')
            button = Button(text = 'Click me') 
            self.root.add_widget(button)

        self.assertEqual(self.root.children[0].children[0], button)
    
    def test_dispatch_on_touch_down(self):
        self.root.dispatch('on_touch_down')
    
    def test_dispatch_on_touch_up(self):
        self.root.dispatch('on_touch_up')
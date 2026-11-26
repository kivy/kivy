# test_gl_failure.py
from kivy.app import App
from kivy.uix.label import Label
try:
    class TestApp(App):
        def build(self):
            return Label(text='Test OpenGL Failure')
    TestApp().run()
except SystemExit as e:
    print(f"SystemExit caught with code: {e.code}")
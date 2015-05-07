'''
Scaling Example
================

This example scales a button using PushMatrix and PopMatrix. It shows
a static button with the words 'hello world', stretched about its centre by
a factor of 1.5 horizontally and 5 vertically.
'''


from kivy.app import App
from kivy.lang import Builder

kv = '''
FloatLayout:

    Button:
        text: 'hello world'
        size_hint: None, None
        pos_hint: {'center_x': .5, 'center_y': .5}
        canvas.before:
            PushMatrix
            Scale:
                x: 1.5
                y: 5
                origin: self.center
        canvas.after:
            PopMatrix
'''


class ScalingApp(App):
    def build(self):
        return Builder.load_string(kv)

ScalingApp().run()

# this is for testing angle_stop/angle_start

from kivy.app import App
from kivy.lang import Builder

kv = '''
FloatLayout:

    BoxLayout:
        BoxLayout:
            orientation: 'vertical'
            Slider:
                id: e1
                min: -360.
                max: 360.
            Label:
                text: '{}'.format(e1.value)
        BoxLayout:
            orientation: 'vertical'
            Slider:
                id: e2
                min: -360.
                max: 360.
                value: 360
            Label:
                text: '{}'.format(e2.value)

        ToggleButton:
            id: e3
            text: 'Fast algo\\n(width == height)' if self.state == 'normal' else 'Normal algo\\n(width != height)'

    FloatLayout
        canvas:
            Color:
                rgb: 1, 1, 1
            Ellipse:
                pos: 100, 100
                size: 200, 201 if e3.state == 'down' else 200
                source: 'data/logo/kivy-icon-512.png'
                angle_start: e1.value
                angle_end: e2.value

'''

class CircleApp(App):
    def build(self):
        return Builder.load_string(kv)

CircleApp().run()

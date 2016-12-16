'''
Circle Example
==============

This example exercises circle (ellipse) drawing. You should see sliders at the
top of the screen with the Kivy logo below it. The sliders control the
angle start and stop and the height and width scales. There is a button
to reset the sliders. The logo used for the circle's background image is
from the kivy/data directory. The entire example is coded in the
kv language description.
'''

from kivy.app import App
from kivy.lang import Builder

kv = '''
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: sp(100)
        BoxLayout:
            orientation: 'vertical'
            Slider:
                id: e1
                min: -360.
                max: 360.
            Label:
                text: 'angle_start = {}'.format(e1.value)
        BoxLayout:
            orientation: 'vertical'
            Slider:
                id: e2
                min: -360.
                max: 360.
                value: 360
            Label:
                text: 'angle_end = {}'.format(e2.value)

    BoxLayout:
        size_hint_y: None
        height: sp(100)
        BoxLayout:
            orientation: 'vertical'
            Slider:
                id: wm
                min: 0
                max: 2
                value: 1
            Label:
                text: 'Width mult. = {}'.format(wm.value)
        BoxLayout:
            orientation: 'vertical'
            Slider:
                id: hm
                min: 0
                max: 2
                value: 1
            Label:
                text: 'Height mult. = {}'.format(hm.value)
        Button:
            text: 'Reset ratios'
            on_press: wm.value = 1; hm.value = 1

    FloatLayout:
        canvas:
            Color:
                rgb: 1, 1, 1
            Ellipse:
                pos: 100, 100
                size: 200 * wm.value, 201 * hm.value
                source: 'data/logo/kivy-icon-512.png'
                angle_start: e1.value
                angle_end: e2.value

'''


class CircleApp(App):
    def build(self):
        return Builder.load_string(kv)


CircleApp().run()

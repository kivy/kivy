'''
Texture Wrapping and Coordinates Example
========================================

This example changes texture properties and the properties
of its containing rectangle. You should see some a multicolored
texture with sliders to the left and below and buttons at the
bottom of the screen. The image texture_example_image.png is
rendered into the rectangle. Sliders change the number of copies of the
texture (the tex_coords), the size of enclosing rectangle (the taw_height
and taw_width) while the buttons change how the texture is rendered when more
than one copy is in the rectangle (the
texture_wrap).

'''


from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ListProperty, StringProperty
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.base import runTouchApp


class TextureAccessibleWidget(Widget):
    texture = ObjectProperty(None)
    tex_coords = ListProperty([0, 0, 1, 0, 1, 1, 0, 1])
    texture_wrap = StringProperty('clamp_to_edge')

    def __init__(self, **kwargs):
        super(TextureAccessibleWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.texture_init, 0)

    def texture_init(self, *args):
        self.texture = self.canvas.children[-1].texture

    def on_texture_wrap(self, instance, value):
        self.texture.wrap = value

root = Builder.load_string('''
<TextureAccessibleWidget>:
    canvas:
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'texture_example_image.png'
            tex_coords: root.tex_coords

<SliderWithValue@BoxLayout>:
    min: 0.0
    max: 1.0
    value: slider.value
    Slider:
        id: slider
        orientation: root.orientation
        min: root.min
        max: root.max
        value: 1.0
    Label:
        size_hint: None, None
        size: min(root.size), min(root.size)
        text: str(slider.value)[:4]

BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        SliderWithValue:
            orientation: 'vertical'
            size_hint_x: None
            width: dp(40)
            min: 0
            max: 5
            value: 1
            on_value: taw.tex_coords[5] = self.value
            on_value: taw.tex_coords[7] = self.value
        SliderWithValue:
            orientation: 'vertical'
            size_hint_x: None
            width: dp(40)
            min: 0
            max: taw_container.height
            value: 0.5*taw_container.height
            on_value: taw.height = self.value
        AnchorLayout:
            id: taw_container
            anchor_x: 'left'
            anchor_y: 'bottom'
            TextureAccessibleWidget:
                id: taw
                size_hint: None, None
    BoxLayout:
        size_hint_y: None
        height: dp(80)
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: dp(80)
            Label:
                text: 'size'
                text_size: self.size
                halign: 'right'
                valign: 'middle'
            Label:
                text: 'tex_coords'
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        BoxLayout:
            orientation: 'vertical'
            SliderWithValue:
                min: 0
                max: taw_container.width
                value: 0.5*taw_container.width
                on_value: taw.width = self.value
            SliderWithValue:
                min: 0.
                max: 5.
                value: 1.
                on_value: taw.tex_coords[2] = self.value
                on_value: taw.tex_coords[4] = self.value

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        Label:
            text: 'texture wrap:'
            text_size: self.size
            valign: 'middle'
            halign: 'center'
        Button:
            text: 'clamp_to_edge'
            on_press: taw.texture_wrap = 'clamp_to_edge'
        Button:
            text: 'repeat'
            on_press: taw.texture_wrap = 'repeat'
        Button:
            text: 'mirrored_repeat'
            on_press: taw.texture_wrap = 'mirrored_repeat'
''')

runTouchApp(root)

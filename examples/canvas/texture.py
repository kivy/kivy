'''
Example of changing texture properties and the properties
of its containing rectangle.
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
        print 'children', self.canvas.children
        # self.texture = self.canvas.children[-1].texture
        # self.texture.wrap = 'repeat'

    def update(self, dt):
        tcs = self.tex_coords
        for i in range(0, 8, 2):
            self.tex_coords[i] += dt/3.


root = Builder.load_string('''
<TextureAccessibleWidget>:
    canvas:
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'colours2.png'
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
            Label:
                text: 'tex_coords'
                text_size: self.size
                halign: 'left'
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

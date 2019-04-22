'''
Demonstrate shorten / number of line in label
=============================================

--------------- ------- -------------------------------------------------------
Number of lines Shorten Behavior
--------------- ------- -------------------------------------------------------
0 (unlimited)   False   Default behavior
1               False   Display as much as possible, at least one word
N               False   Display as much as possible
0 (unlimited)   True    Default behavior (as kivy <= 1.7 series)
1               True    Display as much as possible, shorten long word.
N               True    Display as much as possible, shorten long word.
--------------- ------- -------------------------------------------------------

'''


from kivy.app import App
from kivy.lang import Builder

kv = '''
<LabeledSlider@Slider>:
    step: 1
    Label:
        text: '{}'.format(int(root.value))
        size: self.texture_size
        top: root.center_y - sp(20)
        center_x: root.value_pos[0]

BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        spacing: '10dp'
        padding: '4dp'
        size_hint_y: None
        height: '48dp'
        LabeledSlider:
            id: slider
            value: 500
            min: 25
            max: root.width
            on_value: self.value = int(self.value)
        ToggleButton:
            id: shorten
            text: 'Shorten'
        LabeledSlider:
            id: max_lines
            value: 0
            min: 0
            max: 5

    AnchorLayout:
        RelativeLayout:
            size_hint: None, None
            size: slider.value, 50
            canvas:
                Color:
                    rgb: .4, .4, .4
                Rectangle:
                    size: self.size
            Label:
                size_hint: 1, 1
                text_size: self.size
                shorten: shorten.state == 'down'
                max_lines: max_lines.value
                valign: 'middle'
                halign: 'center'
                color: (1, 1, 1, 1)
                font_size: 22
                text: 'Michaelangelo Smith'
'''


class ShortenText(App):
    def build(self):
        return Builder.load_string(kv)


ShortenText().run()

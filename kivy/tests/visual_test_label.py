from kivy.app import runTouchApp
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.utils import get_hex_from_color, get_random_color
import timeit
import re
import random
from functools import partial


def layout_perf(label, repeat):
    if repeat:
        repeat = int(repeat)
    else:
        return 'None'
    return str(timeit.Timer(label._label.render).repeat(1, repeat))


def layout_real_perf(label, repeat):
    if repeat:
        repeat = int(repeat)
    else:
        return 'None'
    old_text = label._label.texture
    label._label.texture = label._label.texture_1px
    res = str(timeit.Timer(partial(label._label.render, True)).repeat(1,
                                                                      repeat))
    label._label.texture = old_text
    return res


kv = '''
#:import tlp visual_test_label.layout_perf
#:import tlrp visual_test_label.layout_real_perf

<TSliderButton@ToggleButton>:
    size_hint: None, None
    size: 100, 50
    group: 'slider'
    on_press: self.parent.slider.name = self.text if self.state =='down' else\
    'dummy'

<TSpinner@Spinner>:
    size_hint: None, None
    size: 100, 50
    name: ''
    on_text: setattr(self.parent.label, self.name, self.text)

<TBoolButton@ToggleButton>:
    size_hint: None, None
    size: 100, 50
    on_state: setattr(self.parent.label, self.text, self.state == 'down')

<TLabel@Label>:
    size_hint: None, None
    size: 100, 50


<LabelTest>:
    cols: 1
    spacing: 10
    padding: 20
    TabbedPanel:
        do_default_tab: False
        tab_width: self.width / 11 * 3
        TabbedPanelItem:
            text: 'Label'
            BoxLayout:
                ScrollView:
                    id: scrollview
                    Label:
                        size_hint: None, None
                        size: self.texture_size
                        id: label
                        text: record.text
                        dummy: 0
                        canvas:
                            Color:
                                rgba: 0, 1, 0, 0.5
                            Rectangle:
                                pos: self.pos
                                size: self.width, self.padding_y
                            Rectangle:
                                pos: self.x, self.y + self.height -\
                                self.padding_y
                                size: self.width, self.padding_y
                            Color:
                                rgba: 0, 0, 1, 0.5
                            Rectangle:
                                pos: self.pos
                                size: self.padding_x, self.height
                            Rectangle:
                                pos: self.x + self.width - self.padding_x,\
                                self.y
                                size: self.padding_x, self.height
                Splitter:
                    sizable_from: 'left'
                    TextInput:
                        id: record
                        text: label.text
                        text: root.text
        TabbedPanelItem:
            text: 'Test performance'
            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: 'Test timeit performance with current label settings'
                BoxLayout:
                    size_hint_y: None
                    height: 40
                    padding: [20, 0]
                    Label:
                        text: 'Repeat count: '
                    TextInput:
                        id: repeat
                        text: '1000'
                    Button:
                        text: 'Go (render - layout)'
                        on_press: results.text = tlp(label, repeat.text)
                    Button:
                        text: 'Go (render_real)'
                        on_press: results.text = tlrp(label, repeat.text)
                Label:
                    id: results
                    text: 'Results:'

    StackLayout:
        id: slider_ctrl
        size_hint_y: None
        height: self.minimum_height
        slider: slider
        label: label
        TLabel:
            text: 'halign: '
        TSpinner:
            name: 'halign'
            values: ['left', 'center', 'right', 'justify']
            text: 'left'
        TLabel:
            text: 'valign: '
        TSpinner:
            name: 'valign'
            values: ['top', 'middle', 'center', 'bottom']
            text: 'bottom'
        TBoolButton:
            text: 'markup'
        TBoolButton:
            text: 'shorten'
        TextInput:
            size_hint: None, None
            size: 100, 50
            hint_text: 'split_str'
            on_text_validate: label.split_str = self.text
            multiline: False
        TLabel:
            text: 'shorten_from: '
        TSpinner:
            name: 'shorten_from'
            values: ['left', 'center', 'right']
            text: 'right'
        TBoolButton:
            text: 'strip'
            state: 'down'
        ToggleButton:
            size_hint: None, None
            size: 100, 50
            text: 'random size'
            on_state: label.text = root.sized_text if self.state == 'down'\
            else root.text
        TLabel:
            text: 'Slider control:'
        TSliderButton:
            text: 'font_size'
        TSliderButton:
            text: 'line_height'
        TSliderButton:
            text: 'max_lines'
        TSliderButton:
            text: 'padding_x'
        TSliderButton:
            text: 'padding_y'
        TextInput:
            size_hint: None, None
            size: 100, 50
            hint_text: 'text_size[0]'
            on_text_validate: label.text_size = (int(self.text) if self.text\
            else None), label.text_size[1]
            multiline: False
        TextInput:
            size_hint: None, None
            size: 100, 50
            hint_text: 'text_size[1]'
            on_text_validate: label.text_size = label.text_size[0],\
            (int(self.text) if self.text else None)
            multiline: False
        TLabel:
            text: '<-- w/ validate'
    Label:
        size_hint_y: None
        height: 40
        color: [0, 1, 0, 1]
        text_size: self.size
        text: 'scrollview size: {}, label size: {}, text_size: {}, '\
        'texture_size: {}, padding: {}'.format(scrollview.size, label.size,\
        label.text_size, label.texture_size, label.padding)

    BoxLayout:
        size_hint_y: None
        height: 40
        Slider:
            id: slider
            range: -10, 200
            value: 15
            name: 'dummy'
            on_value: setattr(label, self.name, self.value)
        Label:
            size_hint_x: None
            width: 50
            text: str(int(slider.value))

'''


text = '''
Because it would spare your Majesty all fear of future \
annoyance. If the lady loves her husband, she does not love your \
Majesty. If she does not love your Majesty, there is no reason \
why she should interfere with your Majesty's plan.

"It is true. And yet--Well! I wish she had been of my own \
station! What a queen she would have made!" He relapsed into a \
moody silence, which was not broken until we drew up in \
Serpentine Avenue.

The door of Briony Lodge was open, and an elderly woman stood \
upon the steps. She watched us with a sardonic eye as we stepped \
from the brougham.

Mr. Sherlock Holmes, I believe?" said she.

I am Mr. Holmes," answered my companion, looking at her with a \
questioning and rather startled gaze.

Indeed! My mistress told me that you were likely to call. She \
left this morning with her husband by the 5:15 train from Charing \
Cross for the Continent."

"What!" Sherlock Holmes staggered back, white with chagrin and \
surprise. "Do you mean that she has left England?"

Never to return.

"And the papers?" asked the King hoarsely. "All is lost."
'''

words = re.split('( +|\\n+)', text)


def annotate(pre, post, callable, words):
    state = False
    i = random.randint(0, 4)
    while i < len(words):
        if ' ' in words[i] or '\n' in words[i]:  # skip spaces
            i += 1
            continue
        if not state:
            words[i] = pre.format(callable(), words[i])
        else:
            words[i] = post.format(words[i])
        state = not state
        i += random.randint(1, 7)


annotate('[size={0}]{1}', '{0}[/size]', partial(random.randint, 8, 24), words)
annotate('[b]{1}', '{0}[/b]', str, words)
annotate('[i]{1}', '{0}[/i]', str, words)
annotate('[color={0}]{1}', '{0}[/color]',
         lambda: get_hex_from_color(get_random_color()), words)
annotated_text = ''.join(words)


class LabelTest(GridLayout):

    text = StringProperty(text)
    sized_text = StringProperty(annotated_text)


if __name__ in ('__main__', ):
    Builder.load_string(kv)
    runTouchApp(LabelTest())

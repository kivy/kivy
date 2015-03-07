'''
Bubble Test
===========

This moves an arrow around in a bubble widget. You should see
a full screen button labelled "Press to show bubble". Clicking shows
a bubble with three bubble buttons of Cut, Copy, and Paste and then moves
the bubble's arrow around. Note that button interior resizes as the arrow is
moved so that the entire bubble and arrow fit into a constant rectangle. Also,
holding the Cut, Copy, or Paste buttons show an on_press change in text.
'''

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.bubble import Bubble

Builder.load_string('''
<cut_copy_paste>
    size_hint: (None, None)
    size: (160, 120)
    pos_hint: {'center_x': .5, 'y': .6}
    BubbleButton:
        text: 'Cut'
        on_press: self.text='Cutting'
        on_release: self.text='Cut'
    BubbleButton:
        text: 'Copy'
        on_press: self.text='Copying'
        on_release: self.text='Copy'
    BubbleButton:
        text: 'Paste'
        on_press: self.text='Pasting'
        on_release: self.text='Paste'
''')


class cut_copy_paste(Bubble):
    pass


class BubbleShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(BubbleShowcase, self).__init__(**kwargs)
        self.but_bubble = Button(text='Press to show bubble')
        self.but_bubble.bind(on_release=self.show_bubble)
        self.add_widget(self.but_bubble)

    def show_bubble(self, *l):
        if not hasattr(self, 'bubb'):
            self.bubb = bubb = cut_copy_paste()
            self.add_widget(bubb)
            self.but_bubble.text = 'Press to change arrow'
        else:
            values = ('left_top', 'left_mid', 'left_bottom', 'top_left',
                'top_mid', 'top_right', 'right_top', 'right_mid',
                'right_bottom', 'bottom_left', 'bottom_mid', 'bottom_right')
            index = values.index(self.bubb.arrow_pos)
            self.bubb.arrow_pos = values[(index + 1) % len(values)]


class TestBubbleApp(App):

    def build(self):
        return BubbleShowcase()

if __name__ == '__main__':
    TestBubbleApp().run()

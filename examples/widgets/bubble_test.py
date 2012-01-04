'''
Bubble
==================

Test of the widget Bubble.

'''

from kivy.app             import App
from kivy.uix.resize      import Re_Size
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout  import GridLayout
from kivy.uix.bubble      import Bubble
from kivy.uix.button      import Button
from kivy.lang            import Builder

Builder.load_string('''
<cut_copy_paste>
    Bubble:
        size_hint: (None, None)
        size: (150, 50)
        arrow_pos: 'top_right'
        #bubb.content.cols = 3
        Button:
            text: 'Cut'
            background_normal: 'data/images/bubble_btn.png'
            border: (0,0,0,0)
        Button:
            text: 'Copy'
            background_normal: 'data/images/bubble_btn.png'
            border: (0,0,0,0)
        Button:
            text: 'Paste'
            background_normal: 'data/images/bubble_btn.png'
            border: (0,0,0,0)
''')

class cut_copy_paste(FloatLayout):
    pass


class BubbleShowcase(FloatLayout):
    def __init__(self, **kwargs):
        super(BubbleShowcase, self).__init__(**kwargs)
        self.but_bubble = Button(text = 'press to show bubble')
        self.but_bubble.bind(on_release = self.show_bubble)
        self.add_widget(self.but_bubble)

    def show_bubble(self, *l):
        bubb = cut_copy_paste()
        self.add_widget(bubb)


class TestBubbleApp(App):
    def build(self):
        return BubbleShowcase()

if __name__ in ('__main__', '__android__'):
    TestBubbleApp().run()

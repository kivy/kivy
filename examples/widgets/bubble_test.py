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


class BubbleShowcase(FloatLayout):
    def __init__(self, **kwargs):
        super(BubbleShowcase, self).__init__(**kwargs)
        self.but_bubble = Button(text = 'press to show bubble')
        self.but_bubble.bind(on_release = self.show_bubble)
        self.add_widget(self.but_bubble)

    def show_bubble(self, *l):
        bubb = Bubble(size_hint = (.27, .0792), arrow_pos = 'bottom_mid')
        #bubb.content.rows = 1
        bubb.content.cols = 3
        bubb.add_widget(Button(text = 'Cut',
                        background_normal = 'data/images/bubble_btn.png',
                        border = (0,0,0,0)))
        bubb.add_widget(Button(text = 'Copy',
                        background_normal = 'data/images/bubble_btn.png',
                        border = (0,0,0,0)))
        bubb.add_widget(Button(text = 'Paste',
                        background_normal = 'data/images/bubble_btn.png',
                        border = (0,0,0,0)))
        self.add_widget(bubb)


class TestBubbleApp(App):
    def build(self):
        return BubbleShowcase()

if __name__ in ('__main__', '__android__'):
    TestBubbleApp().run()

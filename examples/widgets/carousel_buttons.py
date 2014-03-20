'''
Carousel example with button inside.
This is a tiny test for testing the scroll distance/timeout
And ensure the down/up are dispatched if no gesture is done.
'''
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.lang import Builder

Builder.load_string('''
<Page>:
    cols: 3
    Label:
        text: str(id(root))
    Button
    Button
    Button
    Button
        text: 'load(page 3)'
        on_release:
            carousel = root.parent.parent
            carousel.load_slide(carousel.slides[2])
    Button
    Button
        text: 'prev'
        on_release:
            root.parent.parent.load_previous()
    Button
    Button
        text: 'next'
        on_release:
            root.parent.parent.load_next()
''')

class Page(GridLayout):
    pass

class TestApp(App):
    def build(self):
        root = Carousel()
        for x in range(10):
            root.add_widget(Page())
        return root

if __name__ == '__main__':
    TestApp().run()

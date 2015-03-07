'''
Carousel Buttons
================

This example demonstrates a carousel control with ten slides, each a grid
layout of buttons. You should see a grid of buttons with internal id
of the slide in the upper left corner. You can move between screens, or jump
to page 3.
'''
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.lang import Builder

Builder.load_string('''
<Page>:
    cols: 3
    Label:
        text: "id=" + str(id(root))
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

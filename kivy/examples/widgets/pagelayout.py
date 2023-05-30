from kivy.base import runTouchApp
from kivy.lang import Builder

kv = '''
PageLayout:
    BoxLayout:
        canvas:
            Color:
                rgba: 216/255., 195/255., 88/255., 1
            Rectangle:
                pos: self.pos
                size: self.size

        orientation: 'vertical'
        Label:
            size_hint_y: None
            height: 1.5 * self.texture_size[1]
            text: 'page 1'

        Button:
            text: 'test'
            on_press: print("test")

    BoxLayout:
        orientation: 'vertical'
        canvas:
            Color:
                rgba: 109/255., 8/255., 57/255., 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'page 2'

        AsyncImage:
            source: 'http://kivy.org/logos/kivy-logo-black-64.png'

    GridLayout:
        canvas:
            Color:
                rgba: 37/255., 39/255., 30/255., 1
            Rectangle:
                pos: self.pos
                size: self.size

        cols: 2
        Label:
            text: 'page 3'
        AsyncImage:
            source: 'http://kivy.org/slides/kivyandroid-thumb.jpg'
        Button:
            text: 'test'
            on_press: print("test last page")
        AsyncImage:
            source: 'http://kivy.org/slides/kivypictures-thumb.jpg'
        Widget
        AsyncImage:
            source: 'http://kivy.org/slides/particlepanda-thumb.jpg'
'''


if __name__ == '__main__':
    runTouchApp(Builder.load_string(kv))

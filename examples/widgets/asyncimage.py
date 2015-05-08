'''
Asynchronous image loading
==========================

Test of the widget AsyncImage.
We are just putting it in a CenteredAsyncImage for beeing able to center the
image on screen without doing upscale like the original AsyncImage.
'''

from kivy.app import App
from kivy.uix.image import AsyncImage
from kivy.lang import Builder


Builder.load_string('''
<CenteredAsyncImage>:
    size: self.texture_size
    size_hint: None, None
    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
''')


class CenteredAsyncImage(AsyncImage):
    pass


class TestAsyncApp(App):
    def build(self):
        return CenteredAsyncImage(
            source='http://kivy.org/funny-pictures-cat-is-expecting-you.jpg')

if __name__ == '__main__':
    TestAsyncApp().run()

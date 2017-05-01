'''
Asynchronous image loading
==========================

Test of the widget AsyncImage.
We are just putting it in a CenteredAsyncImage for being able to center the
image on screen without doing upscale like the original AsyncImage.
'''

from kivy.app import App
from kivy.uix.image import AsyncImage
from kivy.lang import Builder


Builder.load_string('''
<CenteredAsyncImage>:
    size_hint: 0.8, 0.8
    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
    mipmap: True
''')


class CenteredAsyncImage(AsyncImage):
    pass


class TestAsyncApp(App):
    def build(self):
        url = ('https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/'
               'STS-116_spacewalk_1.jpg/1024px-STS-116_spacewalk_1.jpg')
        return CenteredAsyncImage(source=url)


if __name__ == '__main__':
    TestAsyncApp().run()

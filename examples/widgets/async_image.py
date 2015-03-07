'''
Asynchronous image loading
==========================

This uses the AsyncImage widget. You should see a cat centered on the
screen. The widget creation call returns immediately; the async widget
draws animates a placeholder; downloads the entire image; and,
finally, replaces the placeholder with the downloaded image.

The original cat image is from http://cheezburger.com/2892250368.

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

import kivy
kivy.require('1.2.0')

from sys import argv
from os.path import dirname, join
from kivy.app import App
from kivy.uix.videoplayer import VideoPlayer
from kivy.properties import StringProperty
from kivy.lang import Builder

# check what formats are supported for your targeted devices
# for example try h264 video and acc audo for android using an mp4
# container

KV = '''
GridLayout:
    cols: 2
    Player
    Player
    Player
    Player

<Player@VideoPlayer>:
    source: app.filename
    state: 'play'
    options: {'eos': 'loop'}
'''


class VideoPlayerApp(App):
    filename = StringProperty()

    def build(self):
        if len(argv) > 1:
            self.filename = argv[1]
        else:
            curdir = dirname(__file__)
            self.filename = join(curdir, 'cityCC0.mpg')
        return Builder.load_string(KV)


if __name__ == '__main__':
    VideoPlayerApp().run()

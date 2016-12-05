import kivy
kivy.require('1.2.0')

from sys import argv
from os.path import dirname, join
from kivy.app import App
from kivy.uix.videoplayer import VideoPlayer

#check what formats are supported for your targeted devices
#for example try h264 video and acc audo for android using an mp4
#container


class VideoPlayerApp(App):

    def build(self):
        if len(argv) > 1:
            filename = argv[1]
        else:
            curdir = dirname(__file__)
            filename = join(curdir, 'softboy.mpg')
        return VideoPlayer(source=filename, state='play')


if __name__ == '__main__':
    VideoPlayerApp().run()

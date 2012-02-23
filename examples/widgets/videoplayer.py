import kivy
kivy.require('1.1.2')

from sys import argv
from os.path import dirname, join
from kivy.app import App
from kivy.uix.videoplayer import VideoPlayer


class VideoPlayerApp(App):

    def build(self):
        if len(argv) > 1:
            filename = argv[1]
        else:
            curdir = dirname(__file__)
            filename = join(curdir, 'softboy.avi')
        return VideoPlayer(source=filename, play=True)


if __name__ in ('__main__', '__android__'):
    VideoPlayerApp().run()

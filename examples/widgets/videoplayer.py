import kivy
kivy.require('1.0.4')

from sys import argv
from os.path import dirname, join
from kivy.app import App
from kivy.uix.video import Video
from kivy.uix.scatter import Scatter


class VideoPlayer(App):

    def build(self):
        if len(argv) > 1:
            filename = argv[1]
        else:
            curdir = dirname(__file__)
            filename = join(curdir, 'softboy.avi')
        video = Video(source=filename, play=True)
        scatter = Scatter()
        video.bind(texture_size=scatter.setter('size'))
        scatter.add_widget(video)
        return scatter


if __name__ in ('__main__', '__android__'):
    VideoPlayer().run()

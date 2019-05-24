from kivy.app import App
from kivy.uix.videoplayer import VideoPlayer
from kivy.clock import Clock
import os


class VideoApp(App):

    player = None

    def build(self):
        self.player = player = VideoPlayer(
            source=os.environ['__KIVY_VIDEO_TEST_FNAME'], volume=0)

        self.player.fbind('position', self.check_position)
        Clock.schedule_once(self.start_player, 0)
        Clock.schedule_once(self.stop_player, 5)
        return player

    def start_player(self, *args):
        self.player.state = 'play'

    def check_position(self, *args):
        if self.player.position > 0.1:
            self.stop_player()

    def stop_player(self, *args):
        assert self.player.duration > 0
        assert self.player.position > 0
        self.stop()

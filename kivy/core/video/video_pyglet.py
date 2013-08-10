
'''
VideoPyglet: implementation of VideoBase with Pyglet
'''

import pyglet

from kivy.core.video import VideoBase


#have to set these before importing pyglet.gl
#otherwise pyglet creates a seperate gl context and fails
# on error checks becasue we use pygame window
pyglet.options['shadow_window'] = False
pyglet.options['debug_gl'] = False
import pyglet.gl


class FakePygletContext:
    # another pyglet fix, because pyglet has a bugfix which is a bad hacked,
    # it checks for context._workaround_unpack_row_length..but we're using
    # the implicit context form pyglet or glut window
    # this means we cant have a pyglet window provider though! if we do,
    # this will break pyglet window context
    _workaround_unpack_row_length = False

pyglet.gl.current_context = FakePygletContext()


class VideoPyglet(VideoBase):
    '''VideoBase implementation using Pyglet
    '''

    def unload(self):
        self.player = None
        self._source = None
        self._fbo = None

    def load(self):
        self.unload()  # make sure we unload an resources

        #load media file and set size of video
        self._source = source = pyglet.media.load(self._filename)
        self._format = source.video_format
        self.size = (self._format.width, self._format.height)

        #load pyglet player and have it play teh video we loaded
        self._player = None
        self._player = pyglet.media.Player()
        self._player.queue(source)
        self.play()
        self.stop()

        # we have to keep track of tie ourselves..
        # at least its the only way i can get pyglet player to restart,
        # _player.time does not get reset when you do seek(0) for soe reason,
        # and is read only
        self.time = self._player.time

    def _update(self, dt):
        if self._source.duration - self.time < 0.1:  # we are at the end
            self.seek(0)
        if self.state == 'playing':
            # keep track of time into video
            self.time += dt
            # required by pyglet video if not in pyglet window
            self._player.dispatch_events(dt)
        if self._player.get_texture():
            # TODO: blit the pyglet texture to our own texture.
            assert('TODO')

    def stop(self):
        self._player.pause()
        super(VideoPyglet, self).stop()

    def play(self):
        self._player.play()
        super(VideoPyglet, self).play()

    def seek(self, percent):
        t = self._source.duration * percent
        self.time = t
        self._player.seek(t)
        self.stop()

    def _get_position(self):
        if self._player:
            return self.time

    def _get_duration(self):
        if self._source:
            return self._source.duration

    def _get_volume(self):
        if self._player:
            return self._player.volume
        return 0

    def _set_volume(self, volume):
        if self._player:
            self._player.volume = volume
            self.dispatch('on_frame')



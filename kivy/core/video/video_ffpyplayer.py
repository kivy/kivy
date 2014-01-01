'''
FFmpeg based video abstraction
==============================

To use, you need to install ffpyplyaer and have a compiled ffmpeg shared
library.

    https://github.com/matham/ffpyplayer

The docs there describe how to set this up. But briefly, first you need to
compile ffmpeg using the shared flags while disabling the static flags (you'll
probably have to set the fPIC flag, e.g. CFLAGS=-fPIC). Here's some
instructions: https://trac.ffmpeg.org/wiki/CompilationGuide. For Windows, you
can download compiled GPL binaries from http://ffmpeg.zeranoe.com/builds/.
Similarly, you should download SDL.

Now, you should a ffmpeg and sdl directory. In each, you should have a include,
bin, and lib directory, where e.g. for Windows, lib contains the .dll.a files,
while bin contains the actual dlls. The include directory holds the headers.
The bin directory is only needed if the shared libraries are not already on
the path. In the environment define FFMPEG_ROOT and SDL_ROOT, each pointing to
the ffmpeg, and SDL directories, respectively. (If you're using SDL2,
the include directory will contain a directory called SDL2, which then holds
the headers).

Once defined, download the ffpyplayer git and run

    python setup.py build_ext --inplace

Finally, before running you need to ensure that ffpyplayer is in python's path.

..Note::

    When kivy exits by closing the window while the video is playing,
    it appears that the __del__method of VideoFFPy
    is not called. Because of this the VideoFFPy object is not
    properly deleted when kivy exits. The consequence is that because
    MediaPlayer creates internal threads which do not have their daemon
    flag set, when the main threads exists it'll hang and wait for the other
    MediaPlayer threads to exit. But since __del__ is not called to delete the
    MediaPlayer object, those threads will remain alive hanging kivy. What this
    means is that you have to be sure to delete the MediaPlayer object before
    kivy exits by setting it to None.
'''

__all__ = ('VideoFFPy', )

try:
    import ffpyplayer
    from ffpyplayer.player import MediaPlayer
    from ffpyplayer.tools import set_log_callback, loglevels, get_log_callback
except:
    raise


from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture
from kivy.weakmethod import WeakMethod
import time

Logger.info('VideoFFPy: Using ffpyplayer {}'.format(ffpyplayer.version))


logger_func = {'quiet': Logger.critical, 'panic': Logger.critical,
               'fatal': Logger.critical, 'error': Logger.error,
               'warning': Logger.warning, 'info': Logger.info,
               'verbose': Logger.debug, 'debug': Logger.debug}


def _log_callback(message, level):
    message = message.strip()
    if message:
        logger_func[level]('ffpyplayer: {}'.format(message))


class VideoFFPy(VideoBase):

    def __init__(self, **kwargs):
        self._ffplayer = None
        self._next_frame = None
        self.quitted = False
        self._log_callback_set = False
        self._callback_ref = WeakMethod(self._player_callback)

        if not get_log_callback():
            set_log_callback(_log_callback)
            self._log_callback_set = True

        super(VideoFFPy, self).__init__(**kwargs)

    def __del__(self):
        self.unload()
        if self._log_callback_set:
            set_log_callback(None)

    def _player_callback(self, selector, value):
        if self._ffplayer is None:
            return
        if selector == 'quit':
            def close(*args):
                self.quitted = True
                self.unload()
            Clock.schedule_once(close, 0)

    def _get_position(self):
        if self._ffplayer is not None:
            return self._ffplayer.get_pts()
        return 0

    def _set_position(self, pos):
        self.seek(pos)

    def _get_volume(self):
        if self._ffplayer is not None:
            self._volume = self._ffplayer.get_volume()
        return self._volume

    def _set_volume(self, volume):
        self._volume = volume
        if self._ffplayer is not None:
            self._ffplayer.set_volume(volume)

    def _get_duration(self):
        if self._ffplayer is None:
            return 0
        return self._ffplayer.get_metadata()['duration']

    def _do_eos(self):
        if self.eos == 'pause':
            self.pause()
        elif self.eos == 'stop':
            self.stop()
        elif self.eos == 'loop':
            self.position = 0

        self.dispatch('on_eos')

    def _update(self, dt):
        ffplayer = self._ffplayer
        if not ffplayer:
            return

        if self._next_frame:
            buffer, size, linesizes, pts = self._next_frame
            self.next_frame = None
            if size != self._size or self._texture is None:
                self._texture = Texture.create(size=size, colorfmt='rgb')
                # by adding 'vf':'vflip' to the player initialization
                # ffmpeg will do the flipping
                self._texture.flip_vertical()
                self._size = size
                self.dispatch('on_load')
            self._texture.blit_buffer(buffer)
            self.dispatch('on_frame')
        self._next_frame, val = ffplayer.get_frame()
        if val == 'eof':
            self._do_eos()
            return
        elif val == 'paused':
            return
        Clock.schedule_once(self._update, val if val or self._next_frame
                            else 1 / 30.)

    def seek(self, percent):
        if self._ffplayer is None:
            return
        self._ffplayer.seek(percent * self._ffplayer.get_metadata()
                            ['duration'], relative=False)
        self._next_frame = None
        Clock.unschedule(self._update)
        Clock.schedule_once(self._update, 0)

    def stop(self):
        self.unload()

    def pause(self):
        if self._ffplayer and self._state != 'paused':
            self._ffplayer.toggle_pause()
            self._state = 'paused'

    def play(self):
        if self._ffplayer and self._state == 'paused':
            self._ffplayer.toggle_pause()
            self._state = 'playing'
            Clock.schedule_once(self._update, 0)
            return
        self.load()
        self._ffplayer = MediaPlayer(self._filename,
                                     vid_sink=self._callback_ref,
                                     loglevel='info')
        player = self._ffplayer
        # wait until loaded or failed, shouldn't take long, but just to make
        # sure metadata is available.
        s = time.clock()
        while (player.get_metadata()['src_vid_size'] == (0, 0)
               and not self.quitted and time.clock() - s < 10.):
            time.sleep(0.005)
        self._state = 'playing'
        Clock.schedule_once(self._update, 1 / 30.)

    def load(self):
        self.unload()

    def unload(self):
        Clock.unschedule(self._update)
        if self._ffplayer:
            self._ffplayer = None
        self._next_frame = None
        self._size = (0, 0)
        self._state = ''
        self.quitted = False

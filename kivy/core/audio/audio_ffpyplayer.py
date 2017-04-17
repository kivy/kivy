'''
FFmpeg based audio player
=========================

To use, you need to install ffpyplayer and have a compiled ffmpeg shared
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

    When kivy exits by closing the window while the audio is playing,
    it appears that the __del__method of SoundFFPy
    is not called. Because of this the SoundFFPy object is not
    properly deleted when kivy exits. The consequence is that because
    MediaPlayer creates internal threads which do not have their daemon
    flag set, when the main threads exists it'll hang and wait for the other
    MediaPlayer threads to exit. But since __del__ is not called to delete the
    MediaPlayer object, those threads will remain alive hanging kivy. What this
    means is that you have to be sure to delete the MediaPlayer object before
    kivy exits by setting it to None.
'''

__all__ = ('SoundFFPy', )

try:
    import ffpyplayer
    from ffpyplayer.player import MediaPlayer
    from ffpyplayer.tools import set_log_callback, get_log_callback, formats_in
except:
    raise


from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.audio import Sound, SoundLoader
from kivy.weakmethod import WeakMethod
import time

try:
    Logger.info(
        'SoundFFPy: Using ffpyplayer {}'.format(ffpyplayer.__version__))
except:
    Logger.info('SoundFFPy: Using ffpyplayer {}'.format(ffpyplayer.version))


logger_func = {'quiet': Logger.critical, 'panic': Logger.critical,
               'fatal': Logger.critical, 'error': Logger.error,
               'warning': Logger.warning, 'info': Logger.info,
               'verbose': Logger.debug, 'debug': Logger.debug}


def _log_callback(message, level):
    message = message.strip()
    if message:
        logger_func[level]('ffpyplayer: {}'.format(message))


class SoundFFPy(Sound):

    @staticmethod
    def extensions():
        return formats_in

    def __init__(self, **kwargs):
        self._ffplayer = None
        self.quitted = False
        self._log_callback_set = False
        self._state = ''
        self.state = 'stop'

        if not get_log_callback():
            set_log_callback(_log_callback)
            self._log_callback_set = True

        super(SoundFFPy, self).__init__(**kwargs)

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
        elif selector == 'eof':
            Clock.schedule_once(self._do_eos, 0)

    def load(self):
        self.unload()
        ff_opts = {'vn': True, 'sn': True}  # only audio
        self._ffplayer = MediaPlayer(self.source,
                                     callback=self._player_callback,
                                     loglevel='info', ff_opts=ff_opts)
        player = self._ffplayer
        player.set_volume(self.volume)
        player.toggle_pause()
        self._state = 'paused'
        # wait until loaded or failed, shouldn't take long, but just to make
        # sure metadata is available.
        s = time.clock()
        while ((not player.get_metadata()['duration']) and
               not self.quitted and time.clock() - s < 10.):
            time.sleep(0.005)

    def unload(self):
        if self._ffplayer:
            self._ffplayer = None
        self._state = ''
        self.state = 'stop'
        self.quitted = False

    def play(self):
        if self._state == 'playing':
            super(SoundFFPy, self).play()
            return
        if not self._ffplayer:
            self.load()
        self._ffplayer.toggle_pause()
        self._state = 'playing'
        self.state = 'play'
        super(SoundFFPy, self).play()

    def stop(self):
        if self._ffplayer and self._state == 'playing':
            self._ffplayer.toggle_pause()
            self._state = 'paused'
            self.state = 'stop'
        super(SoundFFPy, self).stop()

    def seek(self, position):
        if self._ffplayer is None:
            return
        self._ffplayer.seek(position, relative=False)

    def get_pos(self):
        if self._ffplayer is not None:
            return self._ffplayer.get_pts()
        return 0

    def on_volume(self, instance, volume):
        if self._ffplayer is not None:
            self._ffplayer.set_volume(volume)

    def _get_length(self):
        if self._ffplayer is None:
            return super(SoundFFPy, self)._get_length()
        return self._ffplayer.get_metadata()['duration']

    def _do_eos(self, *args):
        if not self.loop:
            self.stop()
        else:
            self.seek(0.)


SoundLoader.register(SoundFFPy)

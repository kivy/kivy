'''
FFmpeg based video abstraction
==============================

To use, you need to install ffpyplayer and have a compiled ffmpeg shared
library.

    https://github.com/matham/ffpyplayer

The docs there describe how to set this up. But briefly, first you need to
compile ffmpeg using the shared flags while disabling the static flags (you'll
probably have to set the fPIC flag, e.g. CFLAGS=-fPIC). Here are some
instructions: https://trac.ffmpeg.org/wiki/CompilationGuide. For Windows, you
can download compiled GPL binaries from http://ffmpeg.zeranoe.com/builds/.
Similarly, you should download SDL2.

Now, you should have ffmpeg and sdl directories. In each, you should have an
'include', 'bin' and 'lib' directory, where e.g. for Windows, 'lib' contains
the .dll.a files, while 'bin' contains the actual dlls. The 'include' directory
holds the headers. The 'bin' directory is only needed if the shared libraries
are not already in the path. In the environment, define FFMPEG_ROOT and
SDL_ROOT, each pointing to the ffmpeg and SDL directories respectively. (If
you're using SDL2, the 'include' directory will contain an 'SDL2' directory,
which then holds the headers).

Once defined, download the ffpyplayer git repo and run

    python setup.py build_ext --inplace

Finally, before running you need to ensure that ffpyplayer is in python's path.

..Note::

    When kivy exits by closing the window while the video is playing,
    it appears that the __del__method of VideoFFPy
    is not called. Because of this, the VideoFFPy object is not
    properly deleted when kivy exits. The consequence is that because
    MediaPlayer creates internal threads which do not have their daemon
    flag set, when the main threads exists, it'll hang and wait for the other
    MediaPlayer threads to exit. But since __del__ is not called to delete the
    MediaPlayer object, those threads will remain alive, hanging kivy. What
    this means is that you have to be sure to delete the MediaPlayer object
    before kivy exits by setting it to None.
'''

__all__ = ('VideoFFPy', )

try:
    import ffpyplayer
    from ffpyplayer.player import MediaPlayer
    from ffpyplayer.tools import set_log_callback, get_log_callback
except:
    raise


from threading import Thread
from queue import Queue, Empty, Full
from kivy.clock import Clock, mainthread
from kivy.logger import Logger
from kivy.core.video import VideoBase
from kivy.graphics import Rectangle, BindTexture
from kivy.graphics.texture import Texture
from kivy.graphics.fbo import Fbo
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


if not get_log_callback():
    set_log_callback(_log_callback)


class VideoFFPy(VideoBase):

    YUV_RGB_FS = """
    $HEADER$
    uniform sampler2D tex_y;
    uniform sampler2D tex_u;
    uniform sampler2D tex_v;

    void main(void) {
        float y = texture2D(tex_y, tex_coord0).r;
        float u = texture2D(tex_u, tex_coord0).r - 0.5;
        float v = texture2D(tex_v, tex_coord0).r - 0.5;
        float r = y +             1.402 * v;
        float g = y - 0.344 * u - 0.714 * v;
        float b = y + 1.772 * u;
        gl_FragColor = vec4(r, g, b, 1.0);
    }
    """

    _trigger = None

    def __init__(self, **kwargs):
        self._ffplayer = None
        self._thread = None
        self._next_frame = None
        self._seek_queue = []
        self._ffplayer_need_quit = False
        self._wakeup_queue = Queue(maxsize=1)
        self._trigger = Clock.create_trigger(self._redraw)

        super(VideoFFPy, self).__init__(**kwargs)

    def __del__(self):
        self.unload()

    def _wakeup_thread(self):
        try:
            self._wakeup_queue.put(None, False)
        except Full:
            pass

    def _wait_for_wakeup(self, timeout):
        try:
            self._wakeup_queue.get(True, timeout)
        except Empty:
            pass

    def _player_callback(self, selector, value):
        if self._ffplayer is None:
            return
        if selector == 'quit':
            def close(*args):
                self.unload()
            Clock.schedule_once(close, 0)

    def _get_position(self):
        if self._ffplayer is not None:
            return self._ffplayer.get_pts()
        return 0

    def _set_position(self, pos):
        self.seek(pos)

    def _set_volume(self, volume):
        self._volume = volume
        if self._ffplayer is not None:
            self._ffplayer.set_volume(self._volume)

    def _get_duration(self):
        if self._ffplayer is None:
            return 0
        return self._ffplayer.get_metadata()['duration']

    @mainthread
    def _do_eos(self):
        if self.eos == 'pause':
            self.pause()
        elif self.eos == 'stop':
            self.stop()
        elif self.eos == 'loop':
            # this causes a seek to zero
            self.position = 0

        self.dispatch('on_eos')

    @mainthread
    def _finish_setup(self):
        # once setup is done, we make sure player state matches what user
        # could have requested while player was being setup and it was in limbo
        # also, thread starts player in internal paused mode, so this unpauses
        # it if user didn't request pause meanwhile
        if self._ffplayer is not None:
            self._ffplayer.set_volume(self._volume)
            self._ffplayer.set_pause(self._state == 'paused')
            self._wakeup_thread()

    def _redraw(self, *args):
        if not self._ffplayer:
            return
        next_frame = self._next_frame
        if not next_frame:
            return

        img, pts = next_frame
        if img.get_size() != self._size or self._texture is None:
            self._size = w, h = img.get_size()

            if self._out_fmt == 'yuv420p':
                w2 = int(w / 2)
                h2 = int(h / 2)
                self._tex_y = Texture.create(
                    size=(w, h), colorfmt='luminance')
                self._tex_u = Texture.create(
                    size=(w2, h2), colorfmt='luminance')
                self._tex_v = Texture.create(
                    size=(w2, h2), colorfmt='luminance')
                self._fbo = fbo = Fbo(size=self._size)
                with fbo:
                    BindTexture(texture=self._tex_u, index=1)
                    BindTexture(texture=self._tex_v, index=2)
                    Rectangle(size=fbo.size, texture=self._tex_y)
                fbo.shader.fs = VideoFFPy.YUV_RGB_FS
                fbo['tex_y'] = 0
                fbo['tex_u'] = 1
                fbo['tex_v'] = 2
                self._texture = fbo.texture
            else:
                self._texture = Texture.create(size=self._size,
                                                colorfmt='rgba')

            # XXX FIXME
            # self.texture.add_reload_observer(self.reload_buffer)
            self._texture.flip_vertical()
            self.dispatch('on_load')

        if self._texture:
            if self._out_fmt == 'yuv420p':
                dy, du, dv, _ = img.to_memoryview()
                if dy and du and dv:
                    self._tex_y.blit_buffer(dy, colorfmt='luminance')
                    self._tex_u.blit_buffer(du, colorfmt='luminance')
                    self._tex_v.blit_buffer(dv, colorfmt='luminance')
                    self._fbo.ask_update()
                    self._fbo.draw()
            else:
                self._texture.blit_buffer(
                    img.to_memoryview()[0], colorfmt='rgba')

            self.dispatch('on_frame')

    def _next_frame_run(self, ffplayer):
        sleep = time.sleep
        trigger = self._trigger
        did_dispatch_eof = False
        wait_for_wakeup = self._wait_for_wakeup
        seek_queue = self._seek_queue
        # video starts in internal paused state

        # fast path, if the source video is yuv420p, we'll use a glsl shader
        # for buffer conversion to rgba
        # wait until we get frame metadata
        while not self._ffplayer_need_quit:
            src_pix_fmt = ffplayer.get_metadata().get('src_pix_fmt')
            if not src_pix_fmt:
                wait_for_wakeup(0.005)
                continue

            if src_pix_fmt == 'yuv420p':
                self._out_fmt = 'yuv420p'
                ffplayer.set_output_pix_fmt(self._out_fmt)
            break

        if self._ffplayer_need_quit:
            ffplayer.close_player()
            return

        # wait until loaded or failed, shouldn't take long, but just to make
        # sure metadata is available.
        while not self._ffplayer_need_quit:
            if ffplayer.get_metadata()['src_vid_size'] != (0, 0):
                break
            wait_for_wakeup(0.005)

        if self._ffplayer_need_quit:
            ffplayer.close_player()
            return

        self._ffplayer = ffplayer
        self._finish_setup()
        # now, we'll be in internal paused state and loop will wait until
        # mainthread unpauses us when finishing setup

        while not self._ffplayer_need_quit:
            seek_happened = False
            if seek_queue:
                vals = seek_queue[:]
                del seek_queue[:len(vals)]
                percent, precise = vals[-1]
                ffplayer.seek(
                    percent * ffplayer.get_metadata()['duration'],
                    relative=False,
                    accurate=precise
                )
                seek_happened = True
                did_dispatch_eof = False
                self._next_frame = None

            # Get next frame if paused:
            if seek_happened and ffplayer.get_pause():
                ffplayer.set_volume(0.0)  # Try to do it silently.
                ffplayer.set_pause(False)
                try:
                    # We don't know concrete number of frames to skip,
                    # this number worked fine on couple of tested videos:
                    to_skip = 6
                    while True:
                        frame, val = ffplayer.get_frame(show=False)
                        # Exit loop on invalid val:
                        if val in ('paused', 'eof'):
                            break
                        # Exit loop on seek_queue updated:
                        if seek_queue:
                            break
                        # Wait for next frame:
                        if frame is None:
                            sleep(0.005)
                            continue
                        # Wait until we skipped enough frames:
                        to_skip -= 1
                        if to_skip == 0:
                            break
                    # Assuming last frame is actual, just get it:
                    frame, val = ffplayer.get_frame(force_refresh=True)
                finally:
                    ffplayer.set_pause(bool(self._state == 'paused'))
                    # todo: this is not safe because user could have updated
                    # volume between us reading it and setting it
                    ffplayer.set_volume(self._volume)
            # Get next frame regular:
            else:
                frame, val = ffplayer.get_frame()

            if val == 'eof':
                if not did_dispatch_eof:
                    self._do_eos()
                    did_dispatch_eof = True
                wait_for_wakeup(None)
            elif val == 'paused':
                did_dispatch_eof = False
                wait_for_wakeup(None)
            else:
                did_dispatch_eof = False
                if frame:
                    self._next_frame = frame
                    trigger()
                else:
                    val = val if val else (1 / 30.)
                wait_for_wakeup(val)

        ffplayer.close_player()

    def seek(self, percent, precise=True):
        # still save seek while thread is setting up
        self._seek_queue.append((percent, precise,))
        self._wakeup_thread()

    def stop(self):
        self.unload()

    def pause(self):
        # if state hasn't been set (empty), there's no player. If it's
        # paused, nothing to do so just handle playing
        if self._state == 'playing':
            # we could be in limbo while player is setting up so check. Player
            # will pause when finishing setting up
            if self._ffplayer is not None:
                self._ffplayer.set_pause(True)
            # even in limbo, indicate to start in paused state
            self._state = 'paused'
            self._wakeup_thread()

    def play(self):
        # _state starts empty and is empty again after unloading
        if self._ffplayer:
            # player is already setup, just handle unpausing
            assert self._state in ('paused', 'playing')
            if self._state == 'paused':
                self._ffplayer.set_pause(False)
                self._state = 'playing'
                self._wakeup_thread()
            return

        # we're now either in limbo state waiting for thread to setup,
        # or no thread has been started
        if self._state == 'playing':
            # in limbo, just wait for thread to setup player
            return
        elif self._state == 'paused':
            # in limbo, still unpause for when player becomes ready
            self._state = 'playing'
            self._wakeup_thread()
            return

        # load first unloads
        self.load()
        self._out_fmt = 'rgba'
        # it starts internally paused, but unpauses itself
        ff_opts = {
            'paused': True,
            'out_fmt': self._out_fmt,
            'sn': True,
            'volume': self._volume,
        }
        ffplayer = MediaPlayer(
            self._filename, callback=self._player_callback,
            thread_lib='SDL',
            loglevel='info', ff_opts=ff_opts
        )

        # Disabled as an attempt to fix kivy issue #6210
        # self._ffplayer.set_volume(self._volume)

        self._thread = Thread(
            target=self._next_frame_run,
            name='Next frame',
            args=(ffplayer, )
        )
        # todo: remove
        self._thread.daemon = True

        # start in playing mode, but _ffplayer isn't set until ready. We're
        # now in a limbo state
        self._state = 'playing'
        self._thread.start()

    def load(self):
        self.unload()

    def unload(self):
        # no need to call self._trigger.cancel() because _ffplayer is set
        # to None below, and it's not safe to call clock stuff from __del__

        # if thread is still alive, set it to exit and wake it
        self._wakeup_thread()
        self._ffplayer_need_quit = True
        # wait until it exits
        if self._thread:
            # TODO: use callback, don't block here
            self._thread.join()
            self._thread = None

        if self._ffplayer:
            self._ffplayer = None
        self._next_frame = None
        self._size = (0, 0)
        self._state = ''
        self._seek_queue = []

        # reset for next load since thread is dead for sure
        self._ffplayer_need_quit = False
        self._wakeup_queue = Queue(maxsize=1)

'''
SDL audio provider
==================

This core audio implementation require SDL_mixer library (doesn't care if SDL
1.2 or 1.3 is installed). It might conflict with any other library that are
using SDL_mixer, such as ffmpeg-android.

Currently, this audio provider compilation is activated only for kivy-ios
project.
'''

__all__ = ('SoundSDL', )

from kivy.core.audio import Sound, SoundLoader
from kivy.logger import Logger
from kivy.clock import Clock
from libcpp cimport bool

cdef extern from "SDL.h":
    int SDL_INIT_AUDIO
    int SDL_Init(unsigned int)

cdef extern from "SDL_mixer.h":
    ctypedef struct Mix_Chunk:
        int volume

    void Mix_ChannelFinished((void)(int))

    int Mix_Init(int flags)
    void Mix_Quit()
    int Mix_OpenAudio(int, unsigned short, int, int)
    Mix_Chunk *Mix_LoadWAV(char *)
    void Mix_FreeChunk(Mix_Chunk *)
    int Mix_PlayChannel(int, Mix_Chunk *, int)
    int Mix_HaltChannel(int)
    Mix_Chunk *Mix_GetChunk(int)
    int Mix_Playing(int)

    int MIX_DEFAULT_FORMAT
    int MIX_DEFAULT_FREQUENCY
    int AUDIO_S16SYS
    
cdef int mix_is_init = 0

cdef void channel_finished_cb(int channel) nogil:
    with gil:
        print('Channel finished playing.', channel)

cdef mix_init():
    cdef int audio_rate = 22050
    cdef unsigned short audio_format = AUDIO_S16SYS
    cdef int audio_channels = 2
    cdef int audio_buffers = 4096
    global mix_is_init

    # avoid next call
    if mix_is_init != 0:
        return

    if SDL_Init(SDL_INIT_AUDIO) < 0:
        Logger.critical('AudioSDL: Unable to initialize SDL')
        mix_is_init = -1
        return 0

    Mix_Init(0)

    if Mix_OpenAudio(audio_rate, audio_format, audio_channels, audio_buffers):
        Logger.critical('AudioSDL: Unable to open mixer')
        mix_is_init = -1
        return 0

    #Mix_ChannelFinished(channel_finished_cb)

    mix_is_init = 1
    return 1

cdef class MixContainer:
    cdef Mix_Chunk *chunk
    cdef int channel

    def __init__(self):
        self.chunk = NULL
        self.channel = -1

class SoundSDL(Sound):

    @staticmethod
    def extensions():
        return ('wav', 'ogg')

    def __init__(self, **kwargs):
        self.mc = MixContainer()
        mix_init()
        super(SoundSDL, self).__init__(**kwargs)

    def _check_play(self, dt):
        cdef MixContainer mc = self.mc
        if mc.channel == -1 or mc.chunk == NULL:
            return False
        if Mix_Playing(mc.channel):
            return
        if self.loop:
            def do_loop(dt):
                self.play()
            Clock.schedule_once(do_loop)
        else:
            self.stop()
        return False

    def play(self):
        cdef MixContainer mc = self.mc
        self.stop()
        if mc.chunk == NULL:
            return
        mc.chunk.volume = int(self.volume * 128)
        mc.channel = Mix_PlayChannel(-1, mc.chunk, 0)
        if mc.channel == -1:
            Logger.warning(
                'AudioSDL: Unable to play %r, no more free channel' % self.filename)
            return
        # schedule event to check if the sound is still playing or not
        Clock.schedule_interval(self._check_play, 0.1)
        super(SoundSDL, self).play()

    def stop(self):
        cdef MixContainer mc = self.mc
        if mc.chunk == NULL or mc.channel == -1:
            return
        if Mix_GetChunk(mc.channel) == mc.chunk:
            Mix_HaltChannel(mc.channel)
        mc.channel = -1
        Clock.unschedule(self._check_play)
        super(SoundSDL, self).stop()

    def load(self):
        cdef MixContainer mc = self.mc
        self.unload()
        if self.filename is None:
            return
        mc.chunk = Mix_LoadWAV(<char *><bytes>self.filename)
        if mc.chunk == NULL:
            Logger.warning('AudioSDL: Unable to load %r' % self.filename)
        else:
            mc.chunk.volume = int(self.volume * 128)

    def unload(self):
        cdef MixContainer mc = self.mc
        self.stop()
        if mc.chunk != NULL:
            Mix_FreeChunk(mc.chunk)
            mc.chunk = NULL

    def on_volume(self, instance, volume):
        cdef MixContainer mc = self.mc
        if mc.chunk != NULL:
            mc.chunk.volume = int(volume * 128)

SoundLoader.register(SoundSDL)

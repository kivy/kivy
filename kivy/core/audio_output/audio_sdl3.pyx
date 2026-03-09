'''
SDL3 audio provider
===================

This core audio implementation require SDL_mixer library.
It might conflict with any other library that are using SDL_mixer, such as
ffmpeg-android.

Native formats:

* wav, since 1.9.0

Depending the compilation of SDL3 mixer and/or installed libraries:

* ogg since 1.9.1 (mixer needs libvorbis/libogg)
* flac since 1.9.1 (mixer needs libflac)
* mp3 since 1.9.1 (mixer needs libsmpeg/libmad; only use mad for GPL apps)
  * Since 1.10.1 + mixer 2.0.2, mpg123 can also be used
* sequenced formats since 1.9.1 (midi, mod, s3m, etc. Mixer needs
  libmodplug or libmikmod)

.. Note::

    Sequenced format support changed with mixer v2.0.2. If mixer is
    linked with one of libmodplug or libmikmod, format support for
    both libraries is assumed. This will work perfectly with formats
    supported by both libraries, but if you were to try to load an
    obscure format (like `apun` file with mikmod only), it will fail.

    * Kivy <= 1.10.0: will fail to build with mixer >= 2.0.2
      will report correct format support with < 2.0.2
    * Kivy >= 1.10.1: will build with old and new mixer, and
      will "guesstimate" sequenced format support

.. Warning::

    Sequenced formats use the SDL3 Mixer music channel, you can only play
    one at a time, and .length will be -1 if music fails to load, and 0
    if loaded successfully (we can't get duration of these formats)
'''

__all__ = ('SoundSDL3', 'MusicSDL3')

include "../../../kivy/lib/sdl3.pxi"

from kivy.core.audio_output import Sound, SoundLoader
from kivy.logger import Logger
from kivy.clock import Clock

cdef MIX_Mixer *mixer_instance = NULL


cdef mix_init():
    print("Initializing SDL3 mixer...")
    cdef SDL_AudioSpec desired_spec
    cdef int want_flags = 0
    global mixer_instance

    # avoid next call
    if mixer_instance != NULL:
        return False

    if SDL_Init(SDL_INIT_AUDIO) < 0:
        Logger.critical('AudioSDL3: Unable to initialize SDL: {}'.format(
                        SDL_GetError()))
        return False

    MIX_Init()

    desired_spec.freq = 44100
    desired_spec.format = SDL_AUDIO_S16
    desired_spec.channels = 2
    mixer_instance = MIX_CreateMixerDevice(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &desired_spec)
    if mixer_instance == NULL:
        Logger.critical('AudioSDL3: Unable to open mixer: {}'.format(
                        SDL_GetError()))
        return False
    print("Mixer opened with format: {} Hz, {} channels".format(desired_spec.freq, desired_spec.channels))
    return True

# Container for samples (MIX_LoadAudio)
cdef class ChunkContainer:
    cdef MIX_Audio *chunk
    cdef MIX_Audio *original_chunk
    cdef MIX_Track *track

    def __init__(self):
        self.chunk = NULL
        self.track = MIX_CreateTrack(mixer_instance)

    def __dealloc__(self):
        if self.chunk != NULL:
            if MIX_GetTrackAudio(self.track) == self.chunk:
                MIX_StopTrack(self.track, 0)
            MIX_DestroyAudio(self.chunk)
            self.chunk = NULL
        if self.original_chunk != NULL:
            MIX_DestroyAudio(self.original_chunk)
            self.original_chunk = NULL

# Container for music (MIX_LoadAudio), one channel only
"""
cdef class MusicContainer:
    cdef MIX_Audio *music
    cdef int playing

    def __init__(self):
        self.music = NULL
        self.playing = 0

    def __dealloc__(self):
        if self.music != NULL:
            # I think FreeMusic halts automatically, probably not needed
            if MIX_TrackPlaying() and self.playing:
                MIX_StopTrack()
            MIX_DestroyAudio(self.music)
            self.music = NULL
"""

class SoundSDL3(Sound):
    _provider_name = 'sdl3'

    @staticmethod
    def extensions():
        mix_init()
        extensions = ["wav"]
        extensions.append("flac")
        extensions.append("mp3")
        extensions.append("ogg")
        return extensions

    def __init__(self, **kwargs):
        self._check_play_ev = None
        mix_init()
        self.cc = ChunkContainer()
        super(SoundSDL3, self).__init__(**kwargs)

    def _check_play(self, dt):
        cdef ChunkContainer cc = self.cc
        if cc.track == NULL or cc.chunk == NULL:
            return False
        if MIX_TrackPlaying(cc.track):
            return
        if self.loop:
            def do_loop(dt):
                self.play()
            Clock.schedule_once(do_loop)
        else:
            self.stop()
        return False

    def _get_length(self):
        cdef ChunkContainer cc = self.cc
        cdef int freq, channels
        cdef unsigned int points, frames
        cdef SDL_AudioSpec spec
        if cc.chunk == NULL:
            return 0
        if not MIX_GetMixerFormat(mixer_instance, &spec):
            return 0
        
        points = <unsigned int>int(MIX_GetAudioDuration(cc.chunk) / ((spec.format & 0xFF) / 8))
        frames = <unsigned int>int(points / channels)
        return <double>frames / <double>freq

    def on_pitch(self, instance, value):
        cdef ChunkContainer cc = self.cc

        cdef Uint8 *dst_data = NULL;
        cdef int dst_len = 0;

        cdef SDL_AudioSpec src_spec
        cdef SDL_AudioSpec dst_spec

        if cc.chunk == NULL:
            return

        if not MIX_GetMixerFormat(mixer_instance, &src_spec):
            return

        dst_spec.freq = int(src_spec.freq * value)
        dst_spec.format = src_spec.format
        dst_spec.channels = src_spec.channels

        #if SDL_ConvertAudioSamples(&src_spec, cc.original_chunk.abuf, cc.original_chunk.alen, &dst_spec, &dst_data, &dst_len) < 0:
        #    Logger.warning("SoundSDL3: Error converting audio samples: %s" % SDL_GetError())
        #    return

        # cc.chunk = MIX_LoadRawAudioNoCopy(dst_data, dst_len)
        SDL_free(dst_data)

    def play(self):
        print("Playing sound: {}".format(self.source))
        cdef ChunkContainer cc = self.cc
        self.stop()
        if cc.chunk == NULL:
            return
        MIX_SetTrackGain(cc.track, int(self.volume * 128))
        MIX_SetTrackAudio(cc.track, cc.chunk)
        if not MIX_PlayTrack(cc.track, 0):
            Logger.warning('AudioSDL3: Unable to play {}: {}'.format(
                           self.source, SDL_GetError()))
            return
        # schedule event to check if the sound is still playing or not
        self._check_play_ev = Clock.schedule_interval(self._check_play, 0.1)
        super(SoundSDL3, self).play()

    def stop(self):
        print("Stopping sound: {}".format(self.source))
        cdef ChunkContainer cc = self.cc
        if cc.chunk == NULL or cc.track == NULL:
            return
        if MIX_GetTrackAudio(cc.track) == cc.chunk:
            MIX_StopTrack(cc.track, 0)
        # MIX_DestroyTrack(cc.track)
        if self._check_play_ev is not None:
            self._check_play_ev.cancel()
            self._check_play_ev = None
        super(SoundSDL3, self).stop()

    def load(self):
        print("Loading sound: {}".format(self.source))
        cdef ChunkContainer cc = self.cc
        self.unload()
        if self.source is None:
            return

        if isinstance(self.source, bytes):
            fn = self.source
        else:
            fn = self.source.encode('UTF-8')

        cc.chunk = MIX_LoadAudio(mixer_instance, <char *><bytes>fn, False)
        if cc.chunk == NULL:
            Logger.warning('AudioSDL3: Unable to load {}: {}'.format(
                           self.source, SDL_GetError()))
        else:
            # cc.original_chunk = (cc.chunk.abuf, cc.chunk.alen)
            MIX_SetTrackGain(cc.track, int(self.volume * 128))
            if self.pitch != 1.:
                self.on_pitch(self, self.pitch)

    def unload(self):
        cdef ChunkContainer cc = self.cc
        self.stop()
        if cc.chunk != NULL:
            MIX_DestroyAudio(cc.chunk)
            cc.chunk = NULL

    def on_volume(self, instance, volume):
        cdef ChunkContainer cc = self.cc
        if cc.chunk != NULL:
            MIX_SetTrackGain(cc.track, int(volume * 128))

""""
# LoadMUS supports OGG, MP3, WAV but we only use it for native midi,
# libmikmod, libmodplug and libfluidsynth to avoid confusion
class MusicSDL3(Sound):
    _provider_name = 'sdl3music'

    @staticmethod
    def extensions():
        mix_init()
        # FIXME: this should probably evolve to use the new has_music()
        #        interface to determine format support

        # Assume native midi support (defaults to enabled), but may use
        # modplug, fluidsynth or timidity in reality. It may also be
        # disabled completely, in which case loading it will fail
        extensions = set(['mid', 'midi'])

        # libmodplug and libmikmod, may be incomplete.
        # 0x4 is for mixer < 2.0.2, MIX_INIT_MODPLUG
        extensions.update(['669', 'abc', 'amf', 'ams', 'apun', 'dbm',
                            'dmf', 'dsm', 'far', 'gdm', 'it',   'j2b',
                            'mdl', 'med', 'mod', 'mt2', 'mtm',  'okt',
                            'pat', 'psm', 'ptm', 's3m', 'stm',  'stx',
                            'ult', 'umx', 'uni', 'xm'])

        return list(extensions)

    def __init__(self, **kwargs):
        self.mc = MusicContainer()
        self._check_play_ev = None
        mix_init()
        super(MusicSDL3, self).__init__(**kwargs)

    def _check_play(self, dt):
        cdef MusicContainer mc = self.mc
        if mc.music == NULL:
            return False
        if mc.playing and MIX_TrackPlaying():
            return
        if self.loop:
            def do_loop(dt):
                self.play()
            Clock.schedule_once(do_loop)
        else:
            self.stop()
        return False

    # No way to check length; return -1 if music is loaded, 0 otherwise
    def _get_length(self):
        cdef MusicContainer mc = self.mc
        if mc.music == NULL:
            return -1
        return 0

    def play(self):
        cdef MusicContainer mc = self.mc
        self.stop()
        if mc.music == NULL:
            return
        MIX_SetTrackGain(int(self.volume * 128))
        if MIX_SetTrackAudio(mc.music, 1) == -1:
            Logger.warning('AudioSDL3: Unable to play music {}: {}'.format(
                           self.source, SDL_GetError()))
            return
        MIX_PlayTrack(mc.music, 0)
        mc.playing = 1
        # schedule event to check if the sound is still playing or not
        self._check_play_ev = Clock.schedule_interval(self._check_play, 0.1)
        super(MusicSDL3, self).play()

    def stop(self):
        cdef MusicContainer mc = self.mc
        if mc.music == NULL or not mc.playing:
            return
        MIX_StopTrack()
        mc.playing = 0
        if self._check_play_ev is not None:
            self._check_play_ev.cancel()
            self._check_play_ev = None
        super(MusicSDL3, self).stop()

    def load(self):
        cdef MusicContainer mc = self.mc
        self.unload()
        if self.source is None:
            return

        if isinstance(self.source, bytes):
            fn = self.source
        else:
            fn = self.source.encode('UTF-8')

        mc.music = MIX_LoadAudio(<char *><bytes>fn)
        if mc.music == NULL:
            Logger.warning('AudioSDL3: Unable to load music {}: {}'.format(
                           self.source, SDL_GetError()))
        else:
            MIX_SetTrackGain(int(self.volume * 128))

    def unload(self):
        cdef MusicContainer mc = self.mc
        self.stop()
        if mc.music != NULL:
            MIX_DestroyAudio(mc.music)
            mc.music = NULL

    def on_volume(self, instance, volume):
        cdef MusicContainer mc = self.mc
        if mc.music != NULL and mc.playing:
            MIX_SetTrackGain(int(volume * 128))
"""

SoundLoader.register(SoundSDL3)
# SoundLoader.register(MusicSDL3)

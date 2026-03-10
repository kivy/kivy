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
    return True

cdef class AudioTrackContainer:
    cdef MIX_Audio *audio
    cdef MIX_Track *track

    def __init__(self):
        self.audio = NULL
        self.track = MIX_CreateTrack(mixer_instance)

    def __dealloc__(self):
        if self.audio != NULL:
            if MIX_GetTrackAudio(self.track) == self.audio:
                MIX_StopTrack(self.track, 0)
            MIX_DestroyAudio(self.audio)
            self.audio = NULL

        MIX_DestroyTrack(self.track)
        self.track = NULL


class SoundSDL3(Sound):
    _provider_name = 'sdl3'

    @staticmethod
    def extensions():
        mix_init()
        cdef int decoders_num = MIX_GetNumAudioDecoders()
        cdef char* decoder
        decoders = []
        for i in range(decoders_num):
            decoder = MIX_GetAudioDecoder(i)
            print("Audio decoder {}: {}".format(i, decoder))

        extensions = ["wav"]
        extensions.append("flac")
        extensions.append("mp3")
        extensions.append("ogg")
        return extensions

    def __init__(self, **kwargs):
        self._check_play_ev = None
        mix_init()
        self.audio_track_container = AudioTrackContainer()
        super(SoundSDL3, self).__init__(**kwargs)

    def _check_play(self, dt):
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        if audio_track_container.track == NULL or audio_track_container.audio == NULL:
            return False
        if MIX_TrackPlaying(audio_track_container.track):
            return
        if self.loop:
            def do_loop(dt):
                self.play()
            Clock.schedule_once(do_loop)
        else:
            self.stop()
        return False

    def _get_length(self):
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        cdef int freq, channels
        cdef unsigned int points, frames
        cdef SDL_AudioSpec spec
        if audio_track_container.audio == NULL:
            return 0
        if not MIX_GetMixerFormat(mixer_instance, &spec):
            return 0
        
        points = <unsigned int>int(MIX_GetAudioDuration(audio_track_container.audio) / ((spec.format & 0xFF) / 8))
        frames = <unsigned int>int(points / channels)
        return <double>frames / <double>freq

    def on_pitch(self, instance, value):
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        if not MIX_SetTrackFrequencyRatio(audio_track_container.track, value):
            Logger.warning("SoundSDL3: Error setting pitch: %s" % SDL_GetError())
            return

    def play(self):
        print("Playing sound: {}".format(self.source))
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        self.stop()
        if audio_track_container.audio == NULL:
            return
        MIX_SetTrackGain(audio_track_container.track, int(self.volume * 128))
        MIX_SetTrackAudio(audio_track_container.track, audio_track_container.audio)
        if not MIX_PlayTrack(audio_track_container.track, 0):
            Logger.warning('AudioSDL3: Unable to play {}: {}'.format(
                           self.source, SDL_GetError()))
            return
        # schedule event to check if the sound is still playing or not
        self._check_play_ev = Clock.schedule_interval(self._check_play, 0.1)
        super(SoundSDL3, self).play()

    def stop(self):
        print("Stopping sound: {}".format(self.source))
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        if audio_track_container.audio == NULL or audio_track_container.track == NULL:
            return
        if MIX_GetTrackAudio(audio_track_container.track) == audio_track_container.audio:
            MIX_StopTrack(audio_track_container.track, 0)
        if self._check_play_ev is not None:
            self._check_play_ev.cancel()
            self._check_play_ev = None
        super(SoundSDL3, self).stop()

    def load(self):
        print("Loading sound: {}".format(self.source))
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        self.unload()
        if self.source is None:
            return

        if isinstance(self.source, bytes):
            fn = self.source
        else:
            fn = self.source.encode('UTF-8')

        audio_track_container.audio = MIX_LoadAudio(mixer_instance, <char *><bytes>fn, False)
        if audio_track_container.audio == NULL:
            Logger.warning('AudioSDL3: Unable to load {}: {}'.format(
                           self.source, SDL_GetError()))
        else:
            MIX_SetTrackGain(audio_track_container.track, int(self.volume * 128))
            if self.pitch != 1.:
                self.on_pitch(self, self.pitch)

    def unload(self):
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        self.stop()
        if audio_track_container.audio != NULL:
            MIX_DestroyAudio(audio_track_container.audio)
            audio_track_container.audio = NULL

    def on_volume(self, instance, volume):
        cdef AudioTrackContainer audio_track_container = self.audio_track_container
        if audio_track_container.audio != NULL:
            MIX_SetTrackGain(audio_track_container.track, int(volume * 128))

SoundLoader.register(SoundSDL3)

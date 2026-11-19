'''
SDL3 audio provider
===================

This core audio implementation require SDL_mixer library.
It might conflict with any other library that are using SDL_mixer, such as
ffmpeg-android.

Supported formats depend on the decoders that SDL_mixer is compiled with,
but usually include at least WAV, OGG, FLAC and MP3.

The audio device opens when the first SDL3 sound is created, not when Kivy
checks which formats SDL3 supports.

iOS audio session
-----------------

On iOS, opening the audio device sets the app's audio session category. By
default SDL uses ``AVAudioSessionCategoryPlayback`` with the options to mix
with and duck other apps' audio, so Kivy sounds play even when the silent
switch is on. Set the ``KIVY_AUDIO_CATEGORY`` environment variable before
the first sound is loaded to choose another category:

- ``ambient``: silenced by the silent switch, mixes with other apps' audio.
- ``soloambient``: silenced by the silent switch, stops other apps' audio.
- ``playback``: ignores the silent switch, stops other apps' audio.
- ``playandrecord``: for apps that also record audio.

.. versionchanged:: 3.0.0
    Looping is gapless and no longer dispatches ``on_stop`` and ``on_play``
    on every pass. :meth:`~kivy.core.audio_output.Sound.play` no longer
    dispatches ``on_stop`` when the sound wasn't playing. Added
    ``KIVY_AUDIO_CATEGORY``.
'''

__all__ = ('SoundSDL3')

include "../../../kivy/lib/sdl3.pxi"

from os import environ

from kivy.core.audio_output import Sound, SoundLoader
from kivy.logger import Logger
from kivy.clock import Clock

cdef MIX_Mixer *mixer_instance = NULL
cdef bint mix_library_ready = False

_AUDIO_CATEGORIES = {
    'ambient': b'AVAudioSessionCategoryAmbient',
    'soloambient': b'AVAudioSessionCategorySoloAmbient',
    'playback': b'AVAudioSessionCategoryPlayback',
    'playandrecord': b'AVAudioSessionCategoryPlayAndRecord',
}


cdef bint mix_init_library():
    global mix_library_ready

    if mix_library_ready:
        return True

    if not SDL_Init(SDL_INIT_AUDIO):
        Logger.critical('AudioSDL3: Unable to initialize SDL: {}'.format(
                        SDL_GetError()))
        return False

    if not MIX_Init():
        Logger.critical('AudioSDL3: Unable to initialize SDL_mixer: {}'.format(
                        SDL_GetError()))
        return False

    mix_library_ready = True
    return True


cdef set_audio_category_hint():
    category = environ.get('KIVY_AUDIO_CATEGORY')
    if not category:
        return
    value = _AUDIO_CATEGORIES.get(category.lower())
    if value is None:
        Logger.warning(
            'AudioSDL3: Ignoring unknown KIVY_AUDIO_CATEGORY {!r}, expected '
            'one of {}'.format(category, ', '.join(_AUDIO_CATEGORIES)))
        return
    SDL_SetHint(b'SDL_AUDIO_CATEGORY', <bytes>value)


cdef bint mix_open_device():
    cdef SDL_AudioSpec desired_spec
    global mixer_instance

    if mixer_instance != NULL:
        return True

    if not mix_init_library():
        return False

    # SDL reads the hint when it opens the device.
    set_audio_category_hint()

    desired_spec.freq = 44100
    desired_spec.format = SDL_AUDIO_S16
    desired_spec.channels = 2
    mixer_instance = MIX_CreateMixerDevice(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &desired_spec)
    if mixer_instance == NULL:
        Logger.critical('AudioSDL3: Unable to open mixer: {}'.format(
                        SDL_GetError()))
        return False

    return True

cdef class _SDL3AudioTrack:
    """
    This container explicitly maps audio and a track together, as we do
    not need a complex mixer management.

    Once a _SDL3AudioTrack is initialized, a new track on the mixer is created, and will
    be destroyed when the container is deallocated.
    """

    cdef MIX_Audio *audio
    cdef MIX_Track *track

    def __init__(self):
        self.audio = NULL
        self.track = MIX_CreateTrack(mixer_instance)

    def __dealloc__(self):
        if self.audio != NULL:
            MIX_StopTrack(self.track, 0)
            MIX_DestroyAudio(self.audio)
            self.audio = NULL

        MIX_DestroyTrack(self.track)
        self.track = NULL

    def is_playing(self):
        if not self.is_audio_set():
            return False
        return MIX_TrackPlaying(self.track)

    def is_audio_set(self):
        if self.audio == NULL:
            return False
        return True

    def load_audio(self, source):
        if not isinstance(source, bytes):
            source = source.encode('UTF-8')
        self.audio = MIX_LoadAudio(mixer_instance, <char *><bytes>source, False)

        if not self.is_audio_set():
            Logger.warning('AudioSDL3: Unable to load {}: {}'.format(
                           source, SDL_GetError()))
            return False
        
        # Set the loaded audio to the track. We do this here to be sure that the track is always
        # associated with the audio, even if the track is not playing yet.
        MIX_SetTrackAudio(self.track, self.audio)

        return True

    def unload_audio(self):
        if not self.is_audio_set():
            return
        MIX_DestroyAudio(self.audio)
        self.audio = NULL

    def set_volume(self, volume):
        if not self.is_audio_set():
            return
        MIX_SetTrackGain(self.track, volume)

    def set_pitch(self, pitch):
        if not self.is_audio_set():
            return
        if not MIX_SetTrackFrequencyRatio(self.track, pitch):
            Logger.warning("SoundSDL3: Error setting pitch: %s" % SDL_GetError())
    
    def play(self, int loops=0):
        cdef SDL_PropertiesID options
        cdef bint result
        if not self.is_audio_set():
            return
        options = SDL_CreateProperties()
        SDL_SetNumberProperty(options, b'SDL_mixer.play.loops', loops)
        result = MIX_PlayTrack(self.track, options)
        SDL_DestroyProperties(options)
        return result

    def set_loops(self, int loops):
        if not self.is_audio_set():
            return
        if not MIX_SetTrackLoops(self.track, loops):
            Logger.warning("SoundSDL3: Error setting loops: %s" % SDL_GetError())

    def stop(self):
        if not self.is_audio_set():
            return
        return MIX_StopTrack(self.track, 0)

    def seek(self, position):
        if not self.is_audio_set():
            return
        new_position_frame = MIX_AudioMSToFrames(self.audio, int(position * 1000))
        if not MIX_SetTrackPlaybackPosition(self.track, new_position_frame):
            Logger.warning("SoundSDL3: Error seeking: %s" % SDL_GetError())

    def get_pos(self):
        if not self.is_audio_set():
            return 0
        current_position_frames = MIX_GetTrackPlaybackPosition(self.track)
        return MIX_AudioFramesToMS(self.audio, current_position_frames) / 1000.0
    
    def _get_audio_length_frames(self):
        if not self.is_audio_set():
            return 0
        return MIX_GetAudioDuration(self.audio)

    def get_audio_length(self):
        if not self.is_audio_set():
            return 0
        audio_length_frames = self._get_audio_length_frames()
        # MIX_DURATION_UNKNOWN (-1) or MIX_DURATION_INFINITE (-2), e.g. the
        # AIFF decoder never reports a duration.
        if audio_length_frames < 0:
            return 0
        return MIX_AudioFramesToMS(self.audio, audio_length_frames) / 1000.0


class SoundSDL3(Sound):
    _provider_name = 'sdl3'

    @staticmethod
    def extensions():
        if not mix_init_library():
            return []
        cdef int decoders_num = MIX_GetNumAudioDecoders()
        cdef char* decoder
        extensions = set()
        for i in range(decoders_num):
            decoder = <char *>MIX_GetAudioDecoder(i)
            decoder_str = decoder.decode('utf-8')
            if decoder_str == "WAV":
                extensions.add("wav")
            elif decoder_str == "STBVORBIS":
                extensions.add("ogg")
            elif decoder_str == "VORBIS":
                extensions.add("ogg")
            elif decoder_str == "WAVPACK":
                extensions.add("wv")
            elif decoder_str == "VOC":
                extensions.add("voc")
            elif decoder_str == "AIFF":
                extensions.add("aiff")
                extensions.add("aif")
            elif decoder_str == "AU":
                extensions.add("au")
            elif decoder_str == "DRFLAC":
                extensions.add("flac")
            elif decoder_str == "DRMP3":
                extensions.add("mp3")
            elif decoder_str == "SINEWAVE":
                # This is a special decoder that generates a sine wave, we don't want to report it as supported format.
                continue
            elif decoder_str == "RAW":
                # This is a special decoder that loads raw audio data, we don't want to report it as supported format.
                continue
            else:
                Logger.warning("SoundSDL3: Unrecognized audio decoder: %s , you might want to report this to Kivy developers to add support for this format." % decoder)

        return list(extensions)

    def __init__(self, **kwargs):
        self._check_play_ev = None
        mix_open_device()
        self._audiotrack = _SDL3AudioTrack()
        super(SoundSDL3, self).__init__(**kwargs)

    def _check_play(self, dt):
        if not self._audiotrack.is_audio_set():
            return

        if self._audiotrack.is_playing():
            return

        self.stop()
        return False

    def _get_length(self):
        return self._audiotrack.get_audio_length()

    def on_pitch(self, instance, value):
        self._audiotrack.set_pitch(value)

    def on_loop(self, instance, value):
        self._audiotrack.set_loops(-1 if value else 0)

    def play(self):
        self.stop()
        if not self._audiotrack.is_audio_set():
            return
        
        self._audiotrack.set_volume(self.volume)

        if not self._audiotrack.play(-1 if self.loop else 0):
            Logger.warning('AudioSDL3: Unable to play {}: {}'.format(
                           self.source, SDL_GetError()))
            return
        # schedule event to check if the sound is still playing or not
        self._check_play_ev = Clock.schedule_interval(self._check_play, 0.1)
        super(SoundSDL3, self).play()

    def stop(self):
        self._audiotrack.stop()
        if self._check_play_ev is not None:
            self._check_play_ev.cancel()
            self._check_play_ev = None
        if self.state == 'play':
            super(SoundSDL3, self).stop()

    def load(self):
        self.unload()
        if self.source is None:
            return

        if not self._audiotrack.load_audio(self.source):
            return

    def seek(self, position):
        self._audiotrack.seek(position)

    def get_pos(self):
        return self._audiotrack.get_pos()

    def unload(self):
        self.stop()
        self._audiotrack.unload_audio()

    def on_volume(self, instance, volume):
        self._audiotrack.set_volume(volume)

SoundLoader.register(SoundSDL3)

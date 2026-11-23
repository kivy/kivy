'''
Video Gstplayer
===============

.. versionadded:: 1.8.0

.. versionchanged:: 3.0.0
    Rewritten on a new GStreamer core. GStreamer is loaded at run time, so
    every Linux and Windows build of Kivy includes this provider and uses
    the GStreamer the machine has. It plays through ``playbin3`` (local
    files, HTTP, HLS and DASH), shares GL textures with Kivy where it can,
    and reports failures through :meth:`~kivy.core.video.VideoBase.on_error`.

Implementation of :class:`~kivy.core.video.VideoBase` with GStreamer 1.x,
through :mod:`kivy.lib.gstplayer`. It is the video provider on Linux,
including the Raspberry Pi, and an optional one on Windows (after
``mediafoundation``).

**Where GStreamer comes from.** On Linux, from the distribution: install
the playback plugins (on Debian, Ubuntu and Raspberry Pi OS:
``gstreamer1.0-plugins-base``, ``-good``, ``-bad``, ``gstreamer1.0-libav``
and ``gstreamer1.0-gl``). On Windows, from the official ``gstreamer-*``
wheels (``pip install "kivy[gstreamer]"``) or the official installer. The
``KIVY_GSTREAMER_ROOT`` environment variable points Kivy at another
GStreamer build. GStreamer 1.22 or newer is needed on Linux and 1.24 on
Windows; older versions make the provider unavailable, logged once.

**Rendering.** Frames reach Kivy in one of three ways, logged once per
video:

* ``gl``: GStreamer converts frames on the GPU and Kivy draws GStreamer's
  texture directly. Needs GStreamer 1.24 and a desktop GL (WGL) context on
  Windows, or an EGL or GLX context on Linux. With EGL, frames from a
  hardware decoder never leave the GPU (DMABuf import): on the
  Raspberry Pi 5 this is what makes 4K HEVC play at full rate. With GLX
  they are copied, and a warning says so.
* ``nv12``: frames are uploaded as two planes and converted by a shader.
  Used when sharing isn't possible (ANGLE on Windows, older GStreamer).
* ``rgba``: GStreamer converts to RGBA on the CPU. Only for debugging.

Videos recorded on a phone held upright (an ``image-orientation`` tag) are
shown turned the right way, and videos with non-square pixels at their
display size: the texture's size is the size to show the video at.

**Options** (:attr:`kivy.uix.video.Video.options`):

* ``render``: ``'auto'`` (default), ``'gl'``, ``'nv12'`` or ``'rgba'``.
  ``'gl'`` falls back to ``'nv12'`` when sharing fails.
* ``force_sw_decoders``: ``True`` to never use hardware decoders.

Unknown keys are logged once and ignored.

**Live streams** (RTSP, UDP) can't be seeked: ``seek()`` does nothing,
``stop()`` pauses them, and ``play()`` resumes at the live edge.

**Errors.** A file or stream GStreamer can't play stops playback and fires
``on_error`` once, with GStreamer's reason, or ``missing GStreamer plugin:
<name>`` when a decoder or demuxer isn't installed. ``GST_DEBUG=3`` shows
GStreamer's own warnings.
'''

import sys
import time

try:
    from kivy.lib.gstplayer import (
        GstPlayer, GLShare, get_runtime_info, has_gl, init_start,
        init_status, init_wait, filename_to_uri, STATE_NULL, STATE_PAUSED,
        STATE_PLAYING, STATE_CHANGE_NO_PREROLL, STATE_CHANGE_FAILURE)
except ImportError:
    from kivy.core import handle_win_lib_import_error
    handle_win_lib_import_error(
        'VideoGstplayer', 'gst', 'kivy.lib.gstplayer._gstplayer')
    raise
from kivy.lib.gstplayer._policy import (
    BusError, HARDWARE_DECODER_PREFIXES, RENDER_PATHS, SeekQueue,
    cpu_frames_cheaper_on_nv12,
    display_size, error_text,
    orientation_corners, reorient_tex_coords, runtime_known_issue,
    yuv_conversion)
from kivy.clock import Clock
from kivy.core.video import VideoBase
from kivy.graphics import BindTexture, Fbo, Rectangle
from kivy.graphics.texture import Texture
from kivy.logger import Logger

_version, _library, _source = get_runtime_info()
Logger.info('VideoGstplayer: GStreamer {} from {} ({})'.format(
    '.'.join(map(str, _version[:3])), _source, _library))
if _known_issue := runtime_known_issue(_version):
    Logger.warning('VideoGstplayer: ' + _known_issue)

# Initialize now, in the background, rather than on the first load(): this
# module is imported when the app selects its video provider, so the
# first-run plugin scan (seconds, the first time an app runs) overlaps the
# app's own start-up.
init_start()

_KNOWN_OPTIONS = frozenset({'render', 'force_sw_decoders'})
_BASE_KWARGS = frozenset({'filename', 'eos', 'async', 'autoplay', 'fps'})

GL_TEXTURE_2D = 0x0DE1

NV12_FS = '''
$HEADER$
uniform sampler2D tex_uv;
uniform vec4 yuv_coeffs;
uniform vec3 yuv_range;
void main(void) {
    float y = (texture2D(texture0, tex_coord0).r - yuv_range.x) * yuv_range.y;
    // Chroma is centred on 128, which samples as 128/255, not 0.5.
    vec2 uv = (texture2D(tex_uv, tex_coord0).ra - vec2(0.501961)) * yuv_range.z;
    gl_FragColor = vec4(y + yuv_coeffs.x * uv.y,
                        y - yuv_coeffs.y * uv.x - yuv_coeffs.z * uv.y,
                        y + yuv_coeffs.w * uv.x, 1.0);
}
'''



def _to_uri(filename):
    if '://' in filename:
        return filename
    return filename_to_uri(filename)


def _gl_is_es():
    from kivy.graphics.opengl import glGetString, GL_VERSION
    v = glGetString(GL_VERSION)
    v = v.decode('utf-8', 'replace') if isinstance(v, bytes) else str(v)
    return 'OpenGL ES' in v


class VideoGstplayer(VideoBase):
    '''Implementation of :class:`~kivy.core.video.VideoBase` with GStreamer
    (``playbin3``). See the module documentation for platforms, options
    and rendering.

    .. versionchanged:: 3.0.0
        Rewritten; see the module documentation.
    '''

    def __init__(self, **kwargs):
        self._player = None
        self._gl = None
        self._path = None
        self._uri = None
        self._tick = None
        self._seeks = SeekQueue()
        self._reset_stream_state()
        super(VideoGstplayer, self).__init__(**kwargs)
        # VideoBase polls at 1/fps (30 Hz by default), which drops frames of
        # 60 fps video. This provider runs its own every-frame tick while a
        # video is loaded.
        Clock.unschedule(self._update)
        options = self._options or {}
        unknown = sorted(set(options) - _KNOWN_OPTIONS - _BASE_KWARGS)
        if unknown:
            Logger.warning(
                'VideoGstplayer: ignoring unknown options keys {!r}; known '
                'keys: {!r}'.format(unknown, sorted(_KNOWN_OPTIONS)))

    def _reset_stream_state(self):
        self._error_reported = False
        self._pending_error = None
        self._prerolled = False
        self._preroll_pull = False
        self._live = False
        self._buffer_percent = 100
        self._gst_target = None
        self._duration = -1.0
        self._missing = []
        self._gl_textures = {}
        self._ytex = self._uvtex = self._fbo = None
        self._nv12_key = None
        self._rgba_tex = None
        self._present_fbo = self._present_rect = self._present_key = None
        self._orientation = None
        self._replan = False
        self._logged = False
        self._seeks.clear()

    # ---------- options ----------

    def _render_option(self):
        render = (self._options or {}).get('render', 'auto')
        if render not in RENDER_PATHS:
            Logger.warning(
                'VideoGstplayer: unknown render {!r}; using auto'.format(
                    render))
            render = 'auto'
        return render

    # ---------- VideoBase API ----------

    def load(self):
        Logger.debug('VideoGstplayer: Load <{}>'.format(self._filename))
        self._release()
        self._reset_stream_state()
        if not self._filename:
            return
        self._uri = _to_uri(self._filename)
        if self._uri is None:
            self._pending_error = 'invalid file name'
        init_start()
        if self._tick is None:
            self._tick = Clock.schedule_interval(self._on_tick, 0)
        # A setup failure is reported by _update() on the next tick, not
        # here: load() runs while the Video widget is still constructing
        # this object, before it has bound on_error.
        if self._pending_error is None and init_status()[0] == 'ok':
            self._build()

    def unload(self):
        self._release()
        if self._tick is not None:
            self._tick.cancel()
            self._tick = None
        self._uri = None
        super(VideoGstplayer, self).unload()

    def _release(self):
        if self._player is not None:
            self._player.teardown()
            self._player = None
        self._gl = None
        self._gl_textures = {}
        self._ytex = self._uvtex = self._fbo = None
        self._rgba_tex = None
        self._present_fbo = self._present_rect = self._present_key = None
        self._texture = None

    def play(self):
        super(VideoGstplayer, self).play()
        self._apply_state()

    def pause(self):
        super(VideoGstplayer, self).pause()
        self._apply_state()

    def stop(self):
        super(VideoGstplayer, self).stop()
        if self._player is not None:
            self._apply_state()
            self._request_seek(0.0, False)

    def seek(self, percent, precise=True):
        if self._player is None:
            return
        duration = self._get_duration()
        if duration <= 0:
            return
        self._request_seek(max(0.0, min(1.0, float(percent))) * duration,
                           bool(precise))

    def _get_position(self):
        if self._player is None:
            return 0
        pending = self._seeks.pending
        if pending is not None:
            return pending
        pos = self._player.position()
        return pos if pos >= 0 else 0

    def _get_duration(self):
        if self._player is None:
            return 0
        if self._duration < 0:
            self._duration = self._player.duration()
        return self._duration if self._duration > 0 else 0

    def _set_volume(self, value):
        self._volume = value
        if self._player is not None:
            self._player.set_volume(value)

    # ---------- pipeline ----------

    def _build(self, path=None):
        render = self._render_option() if path is None else path
        force_sw = bool((self._options or {}).get('force_sw_decoders'))
        path, gl = render, None
        if render in ('auto', 'gl'):
            path = 'nv12'
            if not has_gl():
                reason = ('GStreamer has no usable GL library or is older '
                          'than 1.24')
            else:
                try:
                    gl = GLShare(_gl_is_es())
                    path, reason = 'gl', None
                except RuntimeError as e:
                    reason = str(e)
            if reason is not None:
                log = Logger.warning if render == 'gl' else Logger.info
                log('VideoGstplayer: GPU texture sharing unavailable ({}); '
                    'using the nv12 path'.format(reason))
        self._path, self._gl = path, gl
        player = GstPlayer(self._uri, sink=path, force_sw_decoders=force_sw,
                           gl=gl)
        try:
            player.build()
        except RuntimeError as e:
            self._pending_error = str(e)
            return
        self._player = player
        # 'auto' on Linux: look at the decoder after the first preroll and
        # move a software-decoded stream to the nv12 path (D6, spike 4).
        self._replan = (render == 'auto' and path == 'gl' and
                        sys.platform.startswith('linux'))
        player.set_volume(self._volume)
        self._gst_target = None
        self._apply_state()

    def _replan_path(self):
        '''After the first preroll in 'auto': True when the pipeline was
        rebuilt on the nv12 path.'''
        self._replan = False
        info = self._player.describe()
        if not cpu_frames_cheaper_on_nv12(info['decoder_caps'],
                                          info['decoder']):
            return False
        Logger.info(
            'VideoGstplayer: <{}>: {} decodes in software; using the nv12 '
            'path, cheaper than a GL upload for system-memory frames'.format(
                self._filename, info['decoder']))
        self._player.teardown()
        self._player = None
        self._gl = None
        self._gl_textures = {}
        self._present_fbo = self._present_rect = self._present_key = None
        self._logged = False
        self._prerolled = False
        self._build('nv12')
        return True

    def _holding(self):
        '''Held in PAUSED while the buffer refills (not for live streams).'''
        return not self._live and self._buffer_percent < 100

    def _apply_state(self):
        if self._player is None:
            return
        want = STATE_PLAYING if (self._state == 'playing' and
                                 not self._holding()) else STATE_PAUSED
        if want == self._gst_target:
            return
        self._gst_target = want
        ret = self._player.set_state(want)
        if ret == STATE_CHANGE_NO_PREROLL:
            self._live = True
        # A FAILURE is not reported by itself: the element's own error is
        # already on the bus and _update() reports it.

    def _request_seek(self, seconds, accurate):
        if self._live:
            # A live source (RTSP, UDP) has no earlier position to go to:
            # stop() just pauses it and play() resumes at the live edge.
            # A flushing seek would also restart decoding mid-GOP, which
            # v4l2slh265dec before GStreamer 1.26.10 (Raspberry Pi OS)
            # can't survive: it crashes when the first frame's references
            # are missing (raspberrypi/linux#7612, gstreamer!10421).
            return
        target =self._seeks.request((seconds, accurate), time.monotonic(),
                                     ready=self._prerolled)
        if target is not None:
            self._issue_seek(target)

    def _issue_seek(self, target):
        # The pipeline re-prerolls; ASYNC_DONE completes the seek.
        if not self._player.seek(*target):
            self._seeks.failed()

    # ---------- the tick ----------

    def _report(self, text):
        self._error_reported = True
        Logger.error('VideoGstplayer: <{}>: {}'.format(self._filename, text))
        self._release()
        self._do_error(text)

    def _update(self, dt):
        # VideoBase's 1/fps event; unscheduled in __init__. The work is in
        # _on_tick, which runs every frame.
        pass

    def _on_tick(self, dt):
        if self._error_reported or self._uri is None:
            return
        if self._pending_error is not None:
            self._report(self._pending_error)
            return
        if self._player is None:
            state, error = init_status()
            if state == 'error':
                self._report(error)
                return
            if state != 'ok':
                self._set_buffering(self._state == 'playing')
                return
            self._build()
            if self._pending_error is not None:
                self._report(self._pending_error)
                return

        player = self._player
        errors = []
        for m in player.pop_messages():
            kind = m[0]
            if kind == 'error':
                errors.append(BusError(*m[1:]))
            elif kind == 'eos':
                if self._state != '':
                    self._do_eos()
                    if self._player is None:
                        return
            elif kind == 'buffering':
                self._on_buffering_message(m[1])
            elif kind == 'async-done':
                self._on_async_done()
            elif kind == 'duration-changed':
                self._duration = -1.0
            elif kind == 'clock-lost':
                if self._gst_target == STATE_PLAYING:
                    player.set_state(STATE_PAUSED)
                    player.set_state(STATE_PLAYING)
            elif kind == 'missing-plugin':
                self._missing.append(m[1])
            elif kind == 'orientation':
                if m[1] != self._orientation:
                    Logger.info('VideoGstplayer: <{}>: orientation {}'.format(
                        self._filename, m[1]))
                    self._orientation = m[1]
            elif kind == 'warning':
                Logger.warning('VideoGstplayer: {} ({})'.format(m[1], m[2]))
        if errors:
            # The whole bus is drained first: the most specific error can
            # arrive after playbin's generic one.
            self._report(error_text(errors, self._missing))
            return

        got = False
        if self._preroll_pull:
            got = player.pull(preroll=True)
            if got:
                self._preroll_pull = False
        if not got and self._gst_target == STATE_PLAYING:
            got = player.pull()
        if got:
            self._show_frame()

        self._set_buffering(self._state == 'playing' and (
            not self._prerolled or self._holding()))

    def _on_buffering_message(self, percent):
        self._buffer_percent = percent
        if not self._live:
            self._apply_state()

    def _on_async_done(self):
        if self._replan and self._replan_path():
            # The new pipeline prerolls again; a queued seek waits for it.
            return
        self._prerolled = True
        nxt = self._seeks.done(time.monotonic())
        if nxt is not None:
            self._issue_seek(nxt)
            return
        if self._gst_target != STATE_PLAYING:
            # Paused (after load() or a seek): show the preroll frame.
            self._preroll_pull = True

    def _set_buffering(self, value):
        if value != self._buffering:
            self._buffering = value
            self.dispatch('on_buffering', value)

    # ---------- frames ----------

    def _show_frame(self):
        player = self._player
        first = self._texture is None
        if self._path == 'gl':
            self._show_gl(player)
        elif self._path == 'nv12':
            self._show_nv12(player)
        else:
            self._show_rgba(player)
        if self._texture is None:
            return
        if not self._logged:
            self._logged = True
            self._log_path()
        if first:
            self.dispatch('on_load')
        self.dispatch('on_frame')

    def _geometry(self, player):
        '''``(display size, corner permutation or None)`` for the held
        frame: the pixel aspect ratio and the orientation tag applied.'''
        size = display_size(player.width, player.height, player.par_n,
                            player.par_d, self._orientation)
        return size, orientation_corners(self._orientation)

    def _present(self, tex, player):
        '''Show `tex` (upright, at the decoded size). Rotated streams and
        non-square pixels are drawn once more into an Fbo at the display
        size; everything else is shown as is.'''
        size, corners = self._geometry(player)
        if corners is None and size == tuple(tex.size):
            self._present_fbo = None
            self._texture = tex
            return
        key = (size, corners)
        if self._present_fbo is None or self._present_key != key:
            fbo = Fbo(size=size)
            with fbo:
                self._present_rect = Rectangle(size=size, texture=tex)
            self._present_fbo, self._present_key = fbo, key
        coords = tex.tex_coords
        if corners is not None:
            coords = reorient_tex_coords(coords, corners)
        rect = self._present_rect
        rect.texture = tex
        rect.tex_coords = coords
        self._present_fbo.ask_update()
        self._present_fbo.draw()
        self._texture = self._present_fbo.texture

    def _show_gl(self, player):
        tex_id = player.gl_texture_id()
        if not tex_id:
            return
        size = (player.width, player.height)
        tex = self._gl_textures.get(tex_id)
        if tex is None or tex.size != size:
            if tex is not None:
                self._gl_textures = {}
            # GStreamer owns the texture (nofree); its pool reuses a few,
            # so the wrappers are kept by id. The held sample keeps the
            # texture out of the pool until the next frame replaces it.
            tex = Texture(width=size[0], height=size[1],
                          target=GL_TEXTURE_2D, texid=tex_id,
                          colorfmt='rgba', mipmap=False, nofree=True)
            tex.flip_vertical()
            self._gl_textures[tex_id] = tex
        self._present(tex, player)

    def _show_nv12(self, player):
        w, h = player.width, player.height
        if w <= 0 or h <= 0:
            return
        # The NV12 path draws through an Fbo anyway, so rotation and pixel
        # aspect ratio cost nothing extra here.
        size, corners = self._geometry(player)
        key = ((w, h), size, corners, player.colorimetry)
        if self._fbo is None or self._nv12_key != key:
            self._ytex = Texture.create(size=(w, h), colorfmt='luminance')
            self._uvtex = Texture.create(size=((w + 1) // 2, (h + 1) // 2),
                                         colorfmt='luminance_alpha')
            fbo = Fbo(size=size)
            fbo.shader.fs = NV12_FS
            coeffs, rng = yuv_conversion(player.colorimetry, h)
            fbo['tex_uv'] = 1
            fbo['yuv_coeffs'] = [float(c) for c in coeffs]
            fbo['yuv_range'] = [float(r) for r in rng]
            # GStreamer's rows start at the top: flip while drawing.
            coords = (0, 1, 1, 1, 1, 0, 0, 0)
            if corners is not None:
                coords = reorient_tex_coords(coords, corners)
            with fbo:
                BindTexture(texture=self._uvtex, index=1)
                Rectangle(size=size, texture=self._ytex, tex_coords=coords)
            self._fbo, self._nv12_key = fbo, key
            self._texture = fbo.texture
        if player.upload_nv12(self._ytex, self._uvtex):
            self._fbo.ask_update()
            self._fbo.draw()

    def _show_rgba(self, player):
        size = (player.width, player.height)
        if size[0] <= 0 or size[1] <= 0:
            return
        if self._rgba_tex is None or self._rgba_tex.size != size:
            self._rgba_tex = Texture.create(size=size, colorfmt='rgba')
            self._rgba_tex.flip_vertical()
        player.upload_rgba(self._rgba_tex)
        self._present(self._rgba_tex, player)
    def _log_path(self):
        info = self._player.describe()
        detail = ''
        if self._path == 'gl':
            detail = ' ({}, {})'.format(self._gl.platform.upper(),
                                        self._gl.api)
        Logger.info(
            'VideoGstplayer: <{}>: render path {}{}, decoder {}, '
            'decoder output {}{}'.format(
                self._filename, self._path, detail, info['decoder'],
                info['decoder_caps'],
                ', glupload input {}'.format(info['glupload_caps'])
                if self._path == 'gl' else ''))
        decoder = info['decoder'] or ''
        if self._path == 'gl' and self._gl.platform == 'glx' and \
                decoder.startswith(HARDWARE_DECODER_PREFIXES):
            Logger.warning(
                'VideoGstplayer: the hardware decoder {} is used with a GLX '
                'context, so every frame is copied. An EGL context avoids '
                'the copy; Kivy asks for one unless SDL_VIDEO_FORCE_EGL=0, '
                'so EGL was unavailable or turned off.'.format(decoder))

    # ---------- thumbnails ----------

    @classmethod
    def generate_thumbnail(cls, filename, time, size=None):
        '''Generate a thumbnail Texture with GStreamer.

        See :meth:`kivy.core.video.VideoBase.generate_thumbnail`. Blocks
        for at most about 10 seconds (plus GStreamer's first-run plugin
        scan); returns None on any failure.

        .. versionadded:: 3.0.0
        '''
        from kivy.utils import path_to_str
        import time as _time
        filename = path_to_str(filename)
        if not filename:
            return None
        state, _error = init_wait(60)
        if state != 'ok':
            return None
        uri = _to_uri(filename)
        if uri is None:
            return None
        # videoflip applies the orientation tag; its cost doesn't matter for
        # one frame.
        player = GstPlayer(uri, sink='rgba', audio=False, flip=True)
        try:
            player.build()
            if player.set_state(STATE_PAUSED) == STATE_CHANGE_FAILURE:
                return None
            deadline = _time.monotonic() + 10.0

            def wait_preroll():
                while _time.monotonic() < deadline:
                    for m in player.pop_messages():
                        if m[0] == 'error':
                            return False
                        if m[0] == 'async-done':
                            return True
                    _time.sleep(0.005)
                return False

            if not wait_preroll():
                return None
            if time and time > 0:
                # Past the end: the last frame rather than nothing.
                duration = player.duration()
                if duration > 0:
                    time = min(float(time), max(0.0, duration - 0.1))
                if not player.seek(float(time), True) or not wait_preroll():
                    return None
            if not player.pull(preroll=True):
                return None
            w, h = player.width, player.height
            if w <= 0 or h <= 0:
                return None
            tex = Texture.create(size=(w, h), colorfmt='rgba')
            tex.flip_vertical()
            player.upload_rgba(tex)
            shown = display_size(w, h, player.par_n, player.par_d)
        except RuntimeError:
            return None
        finally:
            player.teardown()
        if size is None:
            size = shown
        size = (int(size[0]), int(size[1]))
        if size == (w, h):
            return tex
        fbo = Fbo(size=size)
        with fbo:
            Rectangle(size=size, texture=tex)
        fbo.draw()
        return fbo.texture

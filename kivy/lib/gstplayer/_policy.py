'''
Decisions of the ``gstplayer`` providers that don't need GStreamer:
the error text shown to the app, the YUV conversion for a stream's
colorimetry, and seek coalescing. Pure Python, so it is unit tested
without a GStreamer runtime.

This is an internal module.
'''

from collections import namedtuple

__all__ = ('BusError', 'error_text', 'yuv_conversion', 'SeekQueue',
           'RENDER_PATHS', 'runtime_known_issue')

RENDER_PATHS = ('auto', 'gl', 'nv12', 'rgba')


def runtime_known_issue(version):
    '''A warning for a GStreamer release with a known bug that can take
    the app down, or None.

    1.28.7 (wheels and installer): when an HLS or DASH pipeline stops
    with a download in flight, adaptivedemux2's download helper drains
    its libsoup context without making it the thread default, and libsoup
    aborts the process (``soup-session.c: message_completed: assertion
    failed``). The error after a missing MPEG-TS demuxer triggers it
    every time. Fixed in 1.28.8 (upstream work item 5296; 1.28.8 has no
    wheels for regular CPython on Windows, so Kivy pins 1.28.9). Nothing
    on Kivy's side avoids it: the drain runs in whichever thread sets the
    pipeline's state, and the context it needs is private to the element.
    '''
    if tuple(version[:3]) == (1, 28, 7):
        return (
            'GStreamer 1.28.7 can abort the process when an HLS or DASH '
            'stream stops (always after a missing MPEG-TS demuxer); use '
            '1.28.9 or newer. See https://gitlab.freedesktop.org/'
            'gstreamer/gstreamer/-/work_items/5296')
    return None


BusError = namedtuple(
    'BusError', 'kind domain code message debug http_status source')
BusError.__doc__ = '''An ERROR message from the bus, as
``GstPlayer.pop_messages()`` returns it (without the leading tag).'''


def error_text(errors, missing_plugins=()):
    '''The one message to report for the errors collected in a tick.

    A missing plugin wins: GStreamer's own error then only says that no
    decoder was found. Otherwise playbin's generic "state change failed"
    loses to any other error, which can arrive after it. The generic
    "internal data stream error" gets the last line of its debug string,
    which names the element and the flow return.
    '''
    if missing_plugins:
        return 'missing GStreamer plugin: ' + ', '.join(
            sorted(set(missing_plugins)))
    if not errors:
        return None
    errors = [e if isinstance(e, BusError) else BusError(*e)
              for e in errors]
    specific = [e for e in errors if e.kind != 'state-change'] or errors
    e = specific[0]
    text = e.message or 'unknown GStreamer error'
    if e.http_status and e.http_status >= 100:
        text = '{} (HTTP {})'.format(text, e.http_status)
    elif e.http_status:
        # libsoup 2 (the 1.24 installer) puts its transport errors in the
        # same field, below 100 (2: name not resolved, 4: can't connect).
        # Its message already says which, so there is nothing to append.
        pass
    elif e.kind == 'stream-failed' and (e.source or '').startswith(
            'souphttpsrc'):
        # With libsoup 3, souphttpsrc only logs (at DEBUG) why a request
        # failed before any HTTP status: name resolution, connection or TLS.
        # The bus then carries nothing more specific than this.
        text = ('Could not connect to the server (the host name could not '
                'be resolved, the connection was refused, or the secure '
                'connection failed)')
    elif e.kind == 'stream-failed' and e.debug:
        lines = [ln.strip() for ln in e.debug.splitlines() if ln.strip()]
        if lines:
            text = '{} ({})'.format(text, lines[-1][-200:])
    return text


# Kr, Kb for each matrix (ITU-R BT.601, BT.709, BT.2020; SMPTE 240M).
_MATRICES = {
    'bt601': (0.299, 0.114),
    'bt709': (0.2126, 0.0722),
    'bt2020': (0.2627, 0.0593),
    'smpte240m': (0.212, 0.087),
}

# Named colorimetries (gst_video_colorimetry_from_string): matrix, full.
_NAMED = {
    'bt601': ('bt601', False),
    'bt709': ('bt709', False),
    'smpte240m': ('smpte240m', False),
    'bt2020': ('bt2020', False),
    'bt2020-10': ('bt2020', False),
    'bt2100-pq': ('bt2020', False),
    'bt2100-hlg': ('bt2020', False),
    'srgb': ('bt709', True),
}

# Numeric form "range:matrix:transfer:primaries".
_NUMERIC_MATRIX = {3: 'bt709', 4: 'bt601', 5: 'smpte240m', 6: 'bt2020'}


def parse_colorimetry(colorimetry, height):
    '''``(matrix, full_range)`` for a caps ``colorimetry`` string. Unknown
    or missing values fall back to the usual guess: BT.709 from 720 lines
    up, BT.601 below, limited range.'''
    guess = 'bt709' if height >= 720 else 'bt601'
    if not colorimetry:
        return guess, False
    c = colorimetry.strip().lower()
    if c in _NAMED:
        return _NAMED[c]
    parts = c.split(':')
    if len(parts) == 4:
        try:
            rng, mat = int(parts[0]), int(parts[1])
        except ValueError:
            return guess, False
        return _NUMERIC_MATRIX.get(mat, guess), rng == 1
    return guess, False


def yuv_conversion(colorimetry, height):
    '''Shader parameters for NV12 to RGB: ``(coeffs, range)``.

    ``coeffs`` is ``(r_v, g_u, g_v, b_u)`` for
    ``R = Y + r_v V``, ``G = Y - g_u U - g_v V``, ``B = Y + b_u U``;
    ``range`` is ``(y_offset, y_scale, uv_scale)`` applied to the sampled
    values first (U and V are centred on 128/255 before scaling).
    '''
    matrix, full = parse_colorimetry(colorimetry, height)
    kr, kb = _MATRICES[matrix]
    kg = 1.0 - kr - kb
    coeffs = (2.0 * (1.0 - kr),
              2.0 * kb * (1.0 - kb) / kg,
              2.0 * kr * (1.0 - kr) / kg,
              2.0 * (1.0 - kb))
    if full:
        rng = (0.0, 1.0, 1.0)
    else:
        rng = (16.0 / 255.0, 255.0 / 219.0, 255.0 / 224.0)
    return coeffs, rng


# image-orientation tag -> for each corner of the displayed picture, in
# Kivy's order (bottom-left, bottom-right, top-right, top-left), the corner
# of the decoded picture that lands there. Same meaning as GStreamer's
# gst_video_orientation_from_tag() and videoflip: rotate-90 turns the
# picture 90 degrees clockwise, flip-rotate-0 mirrors it left to right,
# flip-rotate-N mirrors it and then turns it N degrees clockwise (checked
# against videoflip's output in spike 9).
_ORIENTATIONS = {
    'rotate-0': (0, 1, 2, 3),
    'rotate-90': (1, 2, 3, 0),
    'rotate-180': (2, 3, 0, 1),
    'rotate-270': (3, 0, 1, 2),
    'flip-rotate-0': (1, 0, 3, 2),
    'flip-rotate-90': (0, 3, 2, 1),
    'flip-rotate-180': (3, 2, 1, 0),
    'flip-rotate-270': (2, 1, 0, 3),
}


def orientation_corners(orientation):
    '''The corner permutation for an ``image-orientation`` tag value, or
    None for an unknown value or no rotation.'''
    corners = _ORIENTATIONS.get(orientation)
    if corners is None or corners == (0, 1, 2, 3):
        return None
    return corners


def orientation_swaps_size(orientation):
    '''Whether the orientation turns a W x H picture into H x W.'''
    return orientation in ('rotate-90', 'rotate-270', 'flip-rotate-90',
                           'flip-rotate-270')


def reorient_tex_coords(tex_coords, corners):
    '''Apply a corner permutation to Kivy texture coordinates
    ``(u0, v0, u1, v1, u2, v2, u3, v3)`` (bottom-left first, counter
    clockwise), so that drawing a rectangle with the result shows the
    picture turned as the tag says.'''
    pairs = [tuple(tex_coords[2 * i:2 * i + 2]) for i in range(4)]
    out = []
    for src in corners:
        out.extend(pairs[src])
    return tuple(out)


def display_size(width, height, par_n, par_d, orientation=None):
    '''The size to show a ``width`` x ``height`` picture at: pixel aspect
    ratio applied (widening for wide pixels, heightening for tall ones, so
    no detail is thrown away), then the orientation.'''
    w, h = width, height
    if par_n > 0 and par_d > 0 and par_n != par_d:
        if par_n > par_d:
            w = int(round(width * par_n / float(par_d)))
        else:
            h = int(round(height * par_d / float(par_n)))
    if orientation_swaps_size(orientation):
        w, h = h, w
    return w, h


# Hardware decoder factories (Linux V4L2 and VA-API, NVIDIA, Windows D3D,
# Intel Quick Sync). Software decoders (avdec_*, vp9dec, dav1d...) don't
# start with these.
HARDWARE_DECODER_PREFIXES = ('v4l2', 'va', 'nv', 'd3d11', 'd3d12', 'qsv',
                             'msdk')


def cpu_frames_cheaper_on_nv12(decoder_caps, decoder=None):
    '''Whether a stream should leave the GL path for the nv12 one: a
    software decoder whose frames are in plain system memory. Those cost
    less as two plane uploads and a shader than through glupload and
    glcolorconvert (Raspberry Pi 5: 40% vs 66% of a core for 1080p H.264).

    Frames in DMABuf, GL or other GPU memory stay on GL, and so do a
    hardware decoder's frames copied to system memory (a GLX context): on
    Intel Iris Xe nv12 was no cheaper there, and dearer for VP9 (21% vs
    16%).'''
    if not decoder_caps:
        return False
    if decoder and decoder.startswith(HARDWARE_DECODER_PREFIXES):
        return False
    head = decoder_caps.split(',', 1)[0]
    return head.strip() == 'video/x-raw'


class SeekQueue:
    '''At most one seek in flight; later requests replace the queued one.

    A slider being dragged then costs one seek at a time instead of a seek
    per touch event. ``request()`` returns the target to issue now, or None
    when it was queued. ``done()`` (on ASYNC_DONE) returns the queued target
    to issue next, if any. A request equal to the one in flight is dropped
    (``Video.stop()`` followed by ``position = 0``).

    Targets are ``(seconds, accurate)``. ``timeout`` guards against a seek
    whose completion never arrives.
    '''

    def __init__(self, timeout=3.0):
        self.timeout = timeout
        self.in_flight = None
        self.queued = None
        self.started = 0.0

    def request(self, target, now, ready=True):
        if not ready:
            self.queued = target
            return None
        if self.in_flight is not None and \
                now - self.started > self.timeout:
            self.in_flight = None
        if self.in_flight is None:
            self.in_flight = target
            self.started = now
            self.queued = None
            return target
        if target[0] == self.in_flight[0] and self.queued is None:
            return None
        self.queued = target
        return None

    def done(self, now):
        self.in_flight = None
        nxt, self.queued = self.queued, None
        if nxt is not None:
            self.in_flight = nxt
            self.started = now
        return nxt

    def failed(self):
        '''The seek just issued was refused.'''
        self.in_flight = None

    @property
    def pending(self):
        '''The position to report while a seek is pending, or None.'''
        t = self.queued or self.in_flight
        return None if t is None else t[0]

    def clear(self):
        self.in_flight = self.queued = None

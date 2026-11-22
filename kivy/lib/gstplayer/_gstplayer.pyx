'''
GStreamer core for Kivy's ``gstplayer`` video and audio providers.

GStreamer is not linked: its libraries are opened when this module is
imported (see ``_gst_loader.h``), so the module is built without GStreamer
and works with whatever GStreamer 1.x runtime the machine has. Importing
fails, and Kivy selects the next provider, when no usable runtime is found.

Everything here runs on the caller's thread (Kivy's main thread), except
:func:`init_start`, which runs ``gst_init_check()`` on a worker thread
because the first initialization on a machine scans every plugin. There is
no GLib main loop and no callback into Python from GStreamer's threads:
the providers poll the bus and the sink from a Clock event.

This is an internal module; its API may change at any time.
'''

from libc.stdint cimport int64_t, uint64_t, uintptr_t, uint8_t, uint32_t
from libc.string cimport strlen, memset
from cython cimport view as cyview

import os
import sys
import threading
import time
import atexit
import weakref

cdef extern from "_gst_loader.h" nogil:
    ctypedef int kgboolean
    ctypedef unsigned int kguint
    ctypedef uint32_t kGQuark
    ctypedef size_t kGType

    ctypedef struct kGError:
        kGQuark domain
        int code
        char *message

    ctypedef struct kGstElement:
        pass
    ctypedef struct kGstObject:
        pass
    ctypedef struct kGstBus:
        pass
    ctypedef struct kGstCaps:
        pass
    ctypedef struct kGstStructure:
        pass
    ctypedef struct kGstSample:
        pass
    ctypedef struct kGstBuffer:
        pass
    ctypedef struct kGstMemory:
        pass
    ctypedef struct kGstPad:
        pass
    ctypedef struct kGstIterator:
        pass
    ctypedef struct kGstElementFactory:
        pass

    ctypedef struct kGValue:
        kGType g_type

    ctypedef struct kGstMiniObject:
        kGType type
        int refcount

    ctypedef struct kGstMessage:
        kGstMiniObject mini_object
        unsigned int type
        kGstObject *src

    ctypedef struct kGstMapInfo:
        kGstMemory *memory
        uint8_t *data
        size_t size

    ctypedef struct kGstVideoMeta:
        unsigned int width
        unsigned int height
        unsigned int n_planes
        size_t offset[4]
        int stride[4]

    int kgst_load(const char *dir, char *err, size_t errlen)
    int kgst_have_lib(int lib)
    const char *kgst_loaded_path()
    int KGST_LIB_GSTPBUTILS

    # Optional entry points, tested before use.
    bint HAVE_PB_UTILS_INIT "(kgst_api.gst_pb_utils_init != NULL)"
    bint HAVE_MISSING_PLUGIN "(kgst_api.gst_is_missing_plugin_message != NULL && kgst_api.gst_missing_plugin_message_get_description != NULL)"

    void g_free "kgst_api.g_free"(void *mem)
    void g_error_free "kgst_api.g_error_free"(kGError *error)
    void g_object_set "kgst_api.g_object_set"(void *obj, const char *name, ...)
    void g_object_get "kgst_api.g_object_get"(void *obj, const char *name, ...)
    void *g_value_get_object "kgst_api.g_value_get_object"(const kGValue *value)
    void g_value_unset "kgst_api.g_value_unset"(kGValue *value)

    kgboolean gst_init_check "kgst_api.gst_init_check"(int *argc, char ***argv, kGError **error)
    void gst_version "kgst_api.gst_version"(kguint *major, kguint *minor, kguint *micro, kguint *nano)
    kGstElement *gst_element_factory_make "kgst_api.gst_element_factory_make"(const char *factoryname, const char *name)
    kGstElementFactory *gst_element_factory_find "kgst_api.gst_element_factory_find"(const char *name)
    const char *gst_element_factory_get_metadata "kgst_api.gst_element_factory_get_metadata"(kGstElementFactory *factory, const char *key)
    kGstElementFactory *gst_element_get_factory "kgst_api.gst_element_get_factory"(kGstElement *element)
    int gst_element_set_state "kgst_api.gst_element_set_state"(kGstElement *element, int state)
    int gst_element_get_state "kgst_api.gst_element_get_state"(kGstElement *element, int *state, int *pending, uint64_t timeout)
    kGstBus *gst_element_get_bus "kgst_api.gst_element_get_bus"(kGstElement *element)
    kgboolean gst_element_query_position "kgst_api.gst_element_query_position"(kGstElement *element, int format, int64_t *cur)
    kgboolean gst_element_query_duration "kgst_api.gst_element_query_duration"(kGstElement *element, int format, int64_t *duration)
    kgboolean gst_element_seek_simple "kgst_api.gst_element_seek_simple"(kGstElement *element, int format, int flags, int64_t pos)
    kGstPad *gst_element_get_static_pad "kgst_api.gst_element_get_static_pad"(kGstElement *element, const char *name)
    kGstCaps *gst_pad_get_current_caps "kgst_api.gst_pad_get_current_caps"(kGstPad *pad)
    kGstElement *gst_bin_get_by_name "kgst_api.gst_bin_get_by_name"(kGstElement *bin, const char *name)
    kgboolean gst_bin_recalculate_latency "kgst_api.gst_bin_recalculate_latency"(kGstElement *bin)
    kGstIterator *gst_bin_iterate_recurse "kgst_api.gst_bin_iterate_recurse"(kGstElement *bin)
    int gst_iterator_next "kgst_api.gst_iterator_next"(kGstIterator *it, kGValue *elem)
    void gst_iterator_free "kgst_api.gst_iterator_free"(kGstIterator *it)
    kGstElement *gst_parse_launch "kgst_api.gst_parse_launch"(const char *desc, kGError **error)
    kGstElement *gst_parse_bin_from_description "kgst_api.gst_parse_bin_from_description"(const char *desc, kgboolean ghost_unlinked_pads, kGError **err)
    kGstMessage *gst_bus_pop "kgst_api.gst_bus_pop"(kGstBus *bus)
    void gst_message_parse_error "kgst_api.gst_message_parse_error"(kGstMessage *message, kGError **gerror, char **debug)
    void gst_message_parse_warning "kgst_api.gst_message_parse_warning"(kGstMessage *message, kGError **gerror, char **debug)
    void gst_message_parse_error_details "kgst_api.gst_message_parse_error_details"(kGstMessage *message, const kGstStructure **structure)
    void gst_message_parse_buffering "kgst_api.gst_message_parse_buffering"(kGstMessage *message, int *percent)
    void gst_message_parse_state_changed "kgst_api.gst_message_parse_state_changed"(kGstMessage *message, int *oldstate, int *newstate, int *pending)
    const kGstStructure *gst_message_get_structure "kgst_api.gst_message_get_structure"(kGstMessage *message)
    void gst_message_parse_tag "kgst_api.gst_message_parse_tag"(kGstMessage *message, void **tag_list)
    kgboolean gst_tag_list_get_string "kgst_api.gst_tag_list_get_string"(const void *list, const char *tag, char **value)
    kGstMessage *gst_message_new_eos "kgst_api.gst_message_new_eos"(kGstObject *src)
    kgboolean gst_structure_has_name "kgst_api.gst_structure_has_name"(const kGstStructure *structure, const char *name)
    const char *gst_structure_get_string "kgst_api.gst_structure_get_string"(const kGstStructure *structure, const char *fieldname)
    kgboolean gst_structure_get_int "kgst_api.gst_structure_get_int"(const kGstStructure *structure, const char *fieldname, int *value)
    kgboolean gst_structure_get_uint "kgst_api.gst_structure_get_uint"(const kGstStructure *structure, const char *fieldname, kguint *value)
    kgboolean gst_structure_get_fraction "kgst_api.gst_structure_get_fraction"(const kGstStructure *structure, const char *fieldname, int *num, int *den)
    void gst_mini_object_unref "kgst_api.gst_mini_object_unref"(void *mini_object)
    void *gst_object_ref_sink "kgst_api.gst_object_ref_sink"(void *obj)
    void gst_object_unref "kgst_api.gst_object_unref"(void *obj)
    char *gst_object_get_name "kgst_api.gst_object_get_name"(kGstObject *obj)
    char *gst_caps_to_string "kgst_api.gst_caps_to_string"(const kGstCaps *caps)
    kGstStructure *gst_caps_get_structure "kgst_api.gst_caps_get_structure"(const kGstCaps *caps, kguint index)
    kGstBuffer *gst_sample_get_buffer "kgst_api.gst_sample_get_buffer"(kGstSample *sample)
    kGstCaps *gst_sample_get_caps "kgst_api.gst_sample_get_caps"(kGstSample *sample)
    kgboolean gst_buffer_map "kgst_api.gst_buffer_map"(kGstBuffer *buffer, kGstMapInfo *info, int flags)
    void gst_buffer_unmap "kgst_api.gst_buffer_unmap"(kGstBuffer *buffer, kGstMapInfo *info)
    void *gst_buffer_get_meta "kgst_api.gst_buffer_get_meta"(kGstBuffer *buffer, kGType api)
    char *gst_filename_to_uri "kgst_api.gst_filename_to_uri"(const char *filename, kGError **error)
    kGQuark gst_core_error_quark "kgst_api.gst_core_error_quark"()
    kGQuark gst_stream_error_quark "kgst_api.gst_stream_error_quark"()
    kGQuark gst_resource_error_quark "kgst_api.gst_resource_error_quark"()
    kGstSample *gst_app_sink_try_pull_sample "kgst_api.gst_app_sink_try_pull_sample"(kGstElement *appsink, uint64_t timeout)
    kGstSample *gst_app_sink_try_pull_preroll "kgst_api.gst_app_sink_try_pull_preroll"(kGstElement *appsink, uint64_t timeout)
    kGType gst_video_meta_api_get_type "kgst_api.gst_video_meta_api_get_type"()
    void gst_pb_utils_init "kgst_api.gst_pb_utils_init"()
    kgboolean gst_is_missing_plugin_message "kgst_api.gst_is_missing_plugin_message"(kGstMessage *msg)
    char *gst_missing_plugin_message_get_description "kgst_api.gst_missing_plugin_message_get_description"(kGstMessage *msg)


# ---- GStreamer constants (stable across 1.x) ----

STATE_NULL = 1
STATE_READY = 2
STATE_PAUSED = 3
STATE_PLAYING = 4

STATE_CHANGE_FAILURE = 0
STATE_CHANGE_SUCCESS = 1
STATE_CHANGE_ASYNC = 2
STATE_CHANGE_NO_PREROLL = 3

cdef int GST_FORMAT_TIME = 3
cdef int64_t GST_SECOND = 1000000000

cdef unsigned int MSG_EOS = 1 << 0
cdef unsigned int MSG_ERROR = 1 << 1
cdef unsigned int MSG_WARNING = 1 << 2
cdef unsigned int MSG_TAG = 1 << 4
cdef unsigned int MSG_BUFFERING = 1 << 5
cdef unsigned int MSG_STATE_CHANGED = 1 << 6
cdef unsigned int MSG_CLOCK_LOST = 1 << 10
cdef unsigned int MSG_ELEMENT = 1 << 15
cdef unsigned int MSG_DURATION_CHANGED = 1 << 18
cdef unsigned int MSG_LATENCY = 1 << 19
cdef unsigned int MSG_ASYNC_DONE = 1 << 21

cdef int MAP_READ = 1

cdef int SEEK_FLUSH = 1 << 0
cdef int SEEK_ACCURATE = 1 << 1
cdef int SEEK_KEY_UNIT = 1 << 2
cdef int SEEK_SNAP_BEFORE = 1 << 5

cdef unsigned int PLAY_VIDEO = 1 << 0
cdef unsigned int PLAY_AUDIO = 1 << 1
cdef unsigned int PLAY_TEXT = 1 << 2
cdef unsigned int PLAY_SOFT_VOLUME = 1 << 4
cdef unsigned int PLAY_BUFFERING = 1 << 8
cdef unsigned int PLAY_DEINTERLACE = 1 << 9
cdef unsigned int PLAY_FORCE_SW_DECODERS = 1 << 12

cdef int CORE_ERROR_STATE_CHANGE = 4
cdef int STREAM_ERROR_FAILED = 1
cdef int ITERATOR_OK = 1

# Lowest GStreamer accepted. Linux 1.22 brings adaptivedemux2 and a
# non-experimental playbin3. Windows has no distro holding it back, so it
# starts at 1.24 (playbin3 stable).
if sys.platform == 'win32':
    MIN_VERSION = (1, 24)
else:
    MIN_VERSION = (1, 22)


cdef str _s(const char *c):
    if c == NULL:
        return None
    return c[:strlen(c)].decode('utf-8', 'replace')


cdef str _take(char *c):
    '''Decode a string GLib allocated, then free it.'''
    cdef str r
    if c == NULL:
        return None
    r = c[:strlen(c)].decode('utf-8', 'replace')
    g_free(c)
    return r


# ---- Opening the runtime (at import) ----

cdef object _runtime = None   # (version tuple, library path, source label)


cdef _open_runtime():
    global _runtime
    from kivy.lib.gstplayer import _runtime as rt
    cdef char err[1024]
    cdef kguint major = 0, minor = 0, micro = 0, nano = 0
    cdef bytes bdir
    cdef const char *cdir = NULL
    found = rt.find_runtime()
    if found.directory is not None:
        bdir = found.directory.encode('utf-8')
        cdir = bdir
    rt.prepare_environment(found)
    if kgst_load(cdir, err, sizeof(err)) != 0:
        raise ImportError('GStreamer not usable ({}): {}'.format(
            found.source, err.decode('utf-8', 'replace')))
    gst_version(&major, &minor, &micro, &nano)
    version = (major, minor, micro, nano)
    if version[:2] < MIN_VERSION:
        raise ImportError(
            'GStreamer {} ({}) is older than the {} this provider '
            'needs'.format('.'.join(map(str, version[:3])), found.source,
                           '.'.join(map(str, MIN_VERSION))))
    _runtime = (version, _s(kgst_loaded_path()), found.source)


_open_runtime()


def get_gst_version():
    '''The loaded GStreamer version as ``(major, minor, micro, nano)``.'''
    return _runtime[0]


def get_runtime_info():
    '''``(version, library path, source)`` of the loaded GStreamer.'''
    return _runtime


# ---- Initialization on a worker thread ----
#
# The first gst_init on a machine scans every plugin (6 to 13 s with the
# Windows wheels), so gst_init_check() runs on a worker thread, without the
# GIL. GStreamer can be initialized from any thread.

_init_lock = threading.Lock()
_init_done = threading.Event()
_init_state = 'idle'          # 'idle', 'running', 'ok' or 'error'
_init_error = None
_init_seconds = None


cdef bint _selftest():
    '''Check the mirrored GstMessage layout against a real message.'''
    cdef kGstMessage *m = gst_message_new_eos(NULL)
    cdef bint ok
    if m == NULL:
        return False
    ok = m.type == MSG_EOS and m.mini_object.refcount == 1
    gst_mini_object_unref(m)
    return ok


def _init_worker():
    global _init_state, _init_error, _init_seconds
    cdef kGError *err = NULL
    cdef kgboolean ok
    cdef str text = None
    t0 = time.perf_counter()
    with nogil:
        ok = gst_init_check(NULL, NULL, &err)
    if not ok:
        text = 'gst_init_check failed'
        if err != NULL:
            text = '{}: {}'.format(text, _s(err.message))
            g_error_free(err)
    else:
        if HAVE_PB_UTILS_INIT:
            gst_pb_utils_init()
        if not _selftest():
            text = ('GStreamer message layout differs from the one this '
                    'module was written for')
    _init_seconds = time.perf_counter() - t0
    if text is None:
        _init_state = 'ok'
    else:
        _init_error = text
        _init_state = 'error'
    _init_done.set()


def init_start():
    '''Start initializing GStreamer in the background. Idempotent.'''
    global _init_state
    with _init_lock:
        if _init_state != 'idle':
            return
        _init_state = 'running'
    threading.Thread(target=_init_worker, name='kivy-gst-init',
                     daemon=True).start()


def init_status():
    '''``(state, error)``: state is 'idle', 'running', 'ok' or 'error'.'''
    return _init_state, _init_error


def init_wait(timeout=None):
    '''Start initialization if needed and wait for it. Returns
    :func:`init_status`.'''
    init_start()
    _init_done.wait(timeout)
    return init_status()


def init_seconds():
    '''How long ``gst_init_check()`` took, or None before it finished.'''
    return _init_seconds

def filename_to_uri(filename):
    '''``gst_filename_to_uri()``: an absolute ``file://`` URI.'''
    cdef kGError *err = NULL
    cdef bytes b = os.fsencode(filename) if sys.platform != 'win32' \
        else filename.encode('utf-8')
    cdef char *c = gst_filename_to_uri(b, &err)
    if c == NULL:
        if err != NULL:
            g_error_free(err)
        return None
    return _take(c)


def element_available(name):
    '''Whether an element factory exists (GStreamer must be initialized).'''
    cdef bytes b = name.encode('utf-8')
    cdef kGstElementFactory *f = gst_element_factory_find(b)
    if f == NULL:
        return False
    gst_object_unref(f)
    return True


def run_pipeline(description, double timeout=30.0):
    '''Run a ``gst-launch`` style pipeline to EOS. Returns None on success
    or the error text. For tests and tools (generating clips), not for
    playback.'''
    cdef kGError *err = NULL
    cdef bytes b = description.encode('utf-8')
    cdef kGstElement *p = gst_parse_launch(b, &err)
    cdef kGstBus *bus
    cdef kGstMessage *m
    cdef kGError *merr = NULL
    cdef char *dbg = NULL
    if p == NULL:
        return _gerror(err)
    if err != NULL:
        g_error_free(err)   # a warning: the pipeline was still created
    gst_object_ref_sink(p)
    bus = gst_element_get_bus(p)
    result = 'timeout'
    gst_element_set_state(p, STATE_PLAYING)
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            m = gst_bus_pop(bus)
            if m == NULL:
                time.sleep(0.005)
                continue
            if m.type == MSG_EOS:
                result = None
            elif m.type == MSG_ERROR:
                gst_message_parse_error(m, &merr, &dbg)
                result = _gerror(merr)
                if dbg != NULL:
                    g_free(dbg)
                    dbg = NULL
                merr = NULL
            gst_mini_object_unref(m)
            if result != 'timeout':
                break
    finally:
        gst_element_set_state(p, STATE_NULL)
        gst_object_unref(bus)
        gst_object_unref(p)
    return result


cdef str _gerror(kGError *err):
    cdef str text
    if err == NULL:
        return 'no details'
    text = _s(err.message)
    g_error_free(err)
    return text


# ---- The player ----

_players = weakref.WeakSet()

_SINK_PROPS = ('emit-signals=false max-buffers=1 drop=true sync=true '
               'enable-last-sample=false qos=true')

_SINKS = {
    'nv12': ('videoflip video-direction=auto ! '
             'appsink name=kivysink caps="video/x-raw,format=NV12" '
             + _SINK_PROPS),
    'rgba': ('videoflip video-direction=auto ! '
             'appsink name=kivysink caps="video/x-raw,format=RGBA" '
             + _SINK_PROPS),
}


cdef class GstPlayer:
    '''One ``playbin3`` and the sink Kivy reads frames from.

    :Parameters:
        `uri`: str
            A URI (use :func:`filename_to_uri` for files).
        `sink`: str or None
            ``'nv12'`` or ``'rgba'`` for video; None for audio only (no
            video decoding).
        `audio`: bool
            Decode and play audio.
        `force_sw_decoders`: bool
            Set ``playbin3``'s ``force-sw-decoders`` flag.
        `flip`: bool
            Apply the stream's orientation tag with ``videoflip`` in the
            CPU sinks. Off by default: even with no tag to apply,
            ``videoflip`` halved the nv12 frame rate of 4K HEVC on the
            Raspberry Pi 5.
    '''
    cdef kGstElement *pipeline
    cdef kGstElement *sinkbin
    cdef kGstElement *appsink
    cdef kGstBus *bus
    cdef kGstSample *sample
    cdef readonly object uri
    cdef readonly object sink
    cdef readonly bint audio
    cdef readonly bint force_sw_decoders
    cdef readonly bint flip
    cdef readonly int width
    cdef readonly int height
    cdef readonly str format
    cdef readonly str colorimetry
    cdef readonly int par_n
    cdef readonly int par_d
    cdef object __weakref__

    def __cinit__(self):
        self.pipeline = NULL
        self.sinkbin = NULL
        self.appsink = NULL
        self.bus = NULL
        self.sample = NULL
        self.par_n = self.par_d = 1

    def __init__(self, uri, sink='nv12', audio=True,
                 force_sw_decoders=False, flip=False):
        if sink not in (None, 'nv12', 'rgba'):
            raise ValueError('unknown sink {!r}'.format(sink))
        self.uri = uri
        self.sink = sink
        self.audio = audio
        self.force_sw_decoders = force_sw_decoders
        self.flip = flip
        _players.add(self)

    def __dealloc__(self):
        self._free()

    cdef void _free(self):
        if self.pipeline != NULL:
            gst_element_set_state(self.pipeline, STATE_NULL)
        if self.sample != NULL:
            gst_mini_object_unref(self.sample)
            self.sample = NULL
        if self.appsink != NULL:
            gst_object_unref(self.appsink)
            self.appsink = NULL
        if self.sinkbin != NULL:
            gst_object_unref(self.sinkbin)
            self.sinkbin = NULL
        if self.bus != NULL:
            gst_object_unref(self.bus)
            self.bus = NULL
        if self.pipeline != NULL:
            gst_object_unref(self.pipeline)
            self.pipeline = NULL

    def build(self):
        '''Create the pipeline (state NULL). Raises ``RuntimeError`` with a
        reason the app can be shown.'''
        cdef kGError *err = NULL
        cdef unsigned int flags
        cdef bytes buri, bdesc
        if _init_state != 'ok':
            raise RuntimeError(_init_error or 'GStreamer is not initialized')
        if self.pipeline != NULL:
            return
        self.pipeline = gst_element_factory_make(b'playbin3', NULL)
        if self.pipeline == NULL:
            raise RuntimeError('missing GStreamer plugin: playbin3 '
                               '(gst-plugins-base)')
        gst_object_ref_sink(self.pipeline)

        # Not 'soft-colorbalance', which makes playsink add a software
        # converter chain. Not 'text' on Linux: a subtitle overlay would be
        # blended into every frame on the CPU. On Windows 'text' stays on:
        # without it, a stream with a subtitle track (Apple's fMP4 HLS
        # example) never started with the 1.28.7 wheels' default audio sink
        # (wasapi2sink); playbin3 selects the text stream either way.
        flags = PLAY_SOFT_VOLUME | PLAY_BUFFERING | PLAY_DEINTERLACE
        if self.sink is not None and sys.platform == 'win32':
            flags |= PLAY_TEXT
        if self.sink is not None:
            flags |= PLAY_VIDEO
        if self.audio:
            flags |= PLAY_AUDIO
        if self.force_sw_decoders:
            flags |= PLAY_FORCE_SW_DECODERS
        g_object_set(self.pipeline, b'flags', flags, NULL)

        if self.sink is not None:
            desc = _SINKS[self.sink]
            if not self.flip:
                desc = desc.replace('videoflip video-direction=auto ! ', '')
            bdesc = desc.encode('utf-8')
            self.sinkbin = gst_parse_bin_from_description(bdesc, 1, &err)
            if self.sinkbin == NULL:
                text = _gerror(err)
                self._free()
                raise RuntimeError('cannot create the video sink: ' + text)
            gst_object_ref_sink(self.sinkbin)
            self.appsink = gst_bin_get_by_name(self.sinkbin, b'kivysink')
            g_object_set(self.pipeline, b'video-sink', self.sinkbin, NULL)
        buri = self.uri.encode('utf-8')
        g_object_set(self.pipeline, b'uri', <char *>buri, NULL)
        self.bus = gst_element_get_bus(self.pipeline)

    def set_state(self, int state):
        '''``gst_element_set_state()``; returns a STATE_CHANGE_* value.'''
        if self.pipeline == NULL:
            return STATE_CHANGE_FAILURE
        return gst_element_set_state(self.pipeline, state)

    def get_state(self):
        '''``(current, pending)``, without waiting.'''
        cdef int cur = 0, pending = 0
        if self.pipeline == NULL:
            return STATE_NULL, 0
        gst_element_get_state(self.pipeline, &cur, &pending, 0)
        return cur, pending

    def pop_messages(self):
        '''Drain the bus. Returns a list of tuples, oldest first:

        * ``('error', kind, domain, code, message, debug, http_status,
          source)`` with kind ``'state-change'`` (playbin's generic
          "state change failed"), ``'stream-failed'`` (the generic
          "internal data stream error") or ``'other'``
        * ``('warning', message, source)``
        * ``('eos',)``, ``('async-done',)``, ``('duration-changed',)``,
          ``('clock-lost',)``
        * ``('buffering', percent)``
        * ``('missing-plugin', description)``
        * ``('state', old, new)`` for the pipeline itself
        * ``('orientation', value)``: the video stream's
          ``image-orientation`` tag (``'rotate-90'``, ``'flip-rotate-0'``...)
          as Kivy's video sink received it

        ``LATENCY`` is handled here (latency recalculated).
        '''
        cdef kGstMessage *m
        cdef unsigned int t
        cdef list out = []
        if self.bus == NULL:
            return out
        while True:
            m = gst_bus_pop(self.bus)
            if m == NULL:
                break
            t = m.type
            if t == MSG_ERROR:
                out.append(self._error_tuple(m))
            elif t == MSG_WARNING:
                out.append(self._warning_tuple(m))
            elif t == MSG_EOS:
                out.append(('eos',))
            elif t == MSG_BUFFERING:
                out.append(('buffering', self._buffering_percent(m)))
            elif t == MSG_ASYNC_DONE:
                if <void *>m.src == <void *>self.pipeline:
                    out.append(('async-done',))
            elif t == MSG_DURATION_CHANGED:
                out.append(('duration-changed',))
            elif t == MSG_CLOCK_LOST:
                out.append(('clock-lost',))
            elif t == MSG_LATENCY:
                gst_bin_recalculate_latency(self.pipeline)
            elif t == MSG_STATE_CHANGED:
                if <void *>m.src == <void *>self.pipeline:
                    out.append(self._state_tuple(m))
            elif t == MSG_ELEMENT:
                desc = self._missing_plugin(m)
                if desc is not None:
                    out.append(('missing-plugin', desc))
            elif t == MSG_TAG:
                # Every sink posts the tags it receives; only the video
                # sink's describe the picture.
                if self.appsink != NULL and \
                        <void *>m.src == <void *>self.appsink:
                    value = self._orientation(m)
                    if value is not None:
                        out.append(('orientation', value))
            gst_mini_object_unref(m)
        return out

    cdef object _orientation(self, kGstMessage *m):
        cdef void *tags = NULL
        cdef char *value = NULL
        gst_message_parse_tag(m, &tags)
        if tags == NULL:
            return None
        if gst_tag_list_get_string(tags, b'image-orientation', &value):
            result = _take(value)
        else:
            result = None
        gst_mini_object_unref(tags)
        return result

    cdef tuple _error_tuple(self, kGstMessage *m):
        cdef kGError *err = NULL
        cdef char *dbg = NULL
        cdef const kGstStructure *details = NULL
        cdef kguint http = 0
        gst_message_parse_error(m, &err, &dbg)
        gst_message_parse_error_details(m, &details)
        if details != NULL:
            gst_structure_get_uint(details, b'http-status-code', &http)
        domain, kind = 'other', 'other'
        code = 0
        text = None
        if err != NULL:
            code = err.code
            text = _s(err.message)
            if err.domain == gst_core_error_quark():
                domain = 'core'
                if err.code == CORE_ERROR_STATE_CHANGE:
                    kind = 'state-change'
            elif err.domain == gst_stream_error_quark():
                domain = 'stream'
                if err.code == STREAM_ERROR_FAILED:
                    kind = 'stream-failed'
            elif err.domain == gst_resource_error_quark():
                domain = 'resource'
            g_error_free(err)
        return ('error', kind, domain, code, text, _take(dbg), http,
                _take(gst_object_get_name(m.src)) if m.src != NULL else None)

    cdef tuple _warning_tuple(self, kGstMessage *m):
        cdef kGError *err = NULL
        cdef char *dbg = NULL
        gst_message_parse_warning(m, &err, &dbg)
        text = None
        if err != NULL:
            text = _s(err.message)
            g_error_free(err)
        if dbg != NULL:
            g_free(dbg)
        return ('warning', text,
                _take(gst_object_get_name(m.src)) if m.src != NULL else None)

    cdef int _buffering_percent(self, kGstMessage *m):
        cdef int pct = 0
        gst_message_parse_buffering(m, &pct)
        return pct

    cdef tuple _state_tuple(self, kGstMessage *m):
        cdef int old = 0, new = 0, pending = 0
        gst_message_parse_state_changed(m, &old, &new, &pending)
        return ('state', old, new)

    cdef object _missing_plugin(self, kGstMessage *m):
        cdef const kGstStructure *s
        if HAVE_MISSING_PLUGIN:
            if gst_is_missing_plugin_message(m):
                return _take(gst_missing_plugin_message_get_description(m))
            return None
        s = gst_message_get_structure(m)
        if s == NULL or not gst_structure_has_name(s, b'missing-plugin'):
            return None
        return (_s(gst_structure_get_string(s, b'name')) or
                _s(gst_structure_get_string(s, b'detail')) or 'unknown')

    def pull(self, bint preroll=False):
        '''Take the newest frame without waiting: the preroll frame when
        `preroll` (valid in PAUSED), else the next played one. Returns True
        when a new frame is now held.'''
        cdef kGstSample *s
        cdef kGstCaps *caps
        cdef const kGstStructure *st
        cdef int w = 0, h = 0, n = 1, d = 1
        if self.appsink == NULL:
            return False
        if preroll:
            s = gst_app_sink_try_pull_preroll(self.appsink, 0)
        else:
            s = gst_app_sink_try_pull_sample(self.appsink, 0)
        if s == NULL:
            return False
        if self.sample != NULL:
            gst_mini_object_unref(self.sample)
        self.sample = s
        caps = gst_sample_get_caps(s)
        if caps != NULL:
            st = gst_caps_get_structure(caps, 0)
            if st != NULL:
                gst_structure_get_int(st, b'width', &w)
                gst_structure_get_int(st, b'height', &h)
                self.width, self.height = w, h
                self.format = _s(gst_structure_get_string(st, b'format'))
                self.colorimetry = _s(
                    gst_structure_get_string(st, b'colorimetry'))
                if gst_structure_get_fraction(
                        st, b'pixel-aspect-ratio', &n, &d) and n > 0 \
                        and d > 0:
                    self.par_n, self.par_d = n, d
        return True

    def release_frame(self):
        '''Drop the held frame (its buffer goes back to the pool).'''
        if self.sample != NULL:
            gst_mini_object_unref(self.sample)
            self.sample = NULL

    @property
    def has_frame(self):
        return self.sample != NULL

    def upload_rgba(self, texture):
        '''Upload the held RGBA frame into `texture` (its size).'''
        cdef kGstBuffer *buf
        cdef kGstMapInfo info
        cdef kGstVideoMeta *meta
        cdef size_t offset = 0
        cdef int stride = self.width * 4
        if self.sample == NULL or self.width <= 0:
            return False
        buf = gst_sample_get_buffer(self.sample)
        meta = <kGstVideoMeta *>gst_buffer_get_meta(
            buf, gst_video_meta_api_get_type())
        if meta != NULL:
            offset, stride = meta.offset[0], meta.stride[0]
        if not gst_buffer_map(buf, &info, MAP_READ):
            return False
        try:
            texture.blit_buffer(
                _view(info.data + offset,
                      _plane_len(info.size, offset, stride, self.height)),
                size=(self.width, self.height), colorfmt='rgba',
                rowlength=stride)
        finally:
            gst_buffer_unmap(buf, &info)
        return True

    def upload_nv12(self, ytex, uvtex):
        '''Upload the held NV12 frame: Y plane into `ytex` (luminance, full
        size) and the interleaved UV plane into `uvtex` (luminance_alpha,
        half size).'''
        cdef kGstBuffer *buf
        cdef kGstMapInfo info
        cdef kGstVideoMeta *meta
        cdef int w = self.width, h = self.height
        cdef int ystride = (w + 3) & ~3
        cdef int uvstride = ystride
        cdef size_t yoff = 0
        cdef size_t uvoff = <size_t>ystride * ((h + 1) & ~1)
        cdef int cw = (w + 1) // 2, ch = (h + 1) // 2
        if self.sample == NULL or w <= 0 or h <= 0:
            return False
        buf = gst_sample_get_buffer(self.sample)
        meta = <kGstVideoMeta *>gst_buffer_get_meta(
            buf, gst_video_meta_api_get_type())
        if meta != NULL and meta.n_planes >= 2:
            yoff, uvoff = meta.offset[0], meta.offset[1]
            ystride, uvstride = meta.stride[0], meta.stride[1]
        if not gst_buffer_map(buf, &info, MAP_READ):
            return False
        try:
            ytex.blit_buffer(
                _view(info.data + yoff,
                      _plane_len(info.size, yoff, ystride, h)),
                size=(w, h), colorfmt='luminance', rowlength=ystride)
            uvtex.blit_buffer(
                _view(info.data + uvoff,
                      _plane_len(info.size, uvoff, uvstride, ch)),
                size=(cw, ch), colorfmt='luminance_alpha',
                rowlength=uvstride)
        finally:
            gst_buffer_unmap(buf, &info)
        return True

    def position(self):
        '''Position in seconds, or -1 when unknown.'''
        cdef int64_t pos = 0
        if self.pipeline == NULL or not gst_element_query_position(
                self.pipeline, GST_FORMAT_TIME, &pos) or pos < 0:
            return -1.0
        return pos / <double>GST_SECOND

    def duration(self):
        '''Duration in seconds, or -1 when unknown.'''
        cdef int64_t dur = 0
        if self.pipeline == NULL or not gst_element_query_duration(
                self.pipeline, GST_FORMAT_TIME, &dur) or dur < 0:
            return -1.0
        return dur / <double>GST_SECOND

    def seek(self, double seconds, bint accurate=True):
        '''A flushing seek. Returns whether GStreamer accepted it.'''
        cdef int flags = SEEK_FLUSH
        if self.pipeline == NULL:
            return False
        flags |= SEEK_ACCURATE if accurate else (SEEK_KEY_UNIT |
                                                SEEK_SNAP_BEFORE)
        return bool(gst_element_seek_simple(
            self.pipeline, GST_FORMAT_TIME, flags,
            <int64_t>(max(0.0, seconds) * GST_SECOND)))

    def set_volume(self, double volume):
        if self.pipeline != NULL:
            g_object_set(self.pipeline, b'volume', volume, NULL)

    def describe(self):
        '''What GStreamer chose: ``{'decoder', 'decoder_caps'}`` (None
        where not found). For logs.'''
        cdef kGstIterator *it
        cdef kGValue v
        cdef kGstElement *el
        cdef kGstElementFactory *f
        cdef const char *klass
        cdef kGstPad *pad
        cdef kGstCaps *caps
        info = {'decoder': None, 'decoder_caps': None}
        if self.pipeline == NULL:
            return info
        it = gst_bin_iterate_recurse(self.pipeline)
        if it == NULL:
            return info
        while True:
            memset(&v, 0, sizeof(kGValue))
            if gst_iterator_next(it, &v) != ITERATOR_OK:
                break
            el = <kGstElement *>g_value_get_object(&v)
            f = gst_element_get_factory(el) if el != NULL else NULL
            if f != NULL:
                name = _take(gst_object_get_name(<kGstObject *>f))
                klass = gst_element_factory_get_metadata(f, b'klass')
                kl = klass[:strlen(klass)] if klass != NULL else b''
                if b'Decoder' in kl and b'Video' in kl:
                    info['decoder'] = name
                    info['decoder_caps'] = _pad_caps(el, b'src')
            g_value_unset(&v)
        gst_iterator_free(it)
        return info

    def teardown(self):
        '''Set NULL and free everything. Safe to call more than once.'''
        self._free()


cdef object _pad_caps(kGstElement *el, const char *padname):
    cdef kGstPad *pad = gst_element_get_static_pad(el, padname)
    cdef kGstCaps *caps
    if pad == NULL:
        return None
    caps = gst_pad_get_current_caps(pad)
    gst_object_unref(pad)
    if caps == NULL:
        return None
    text = _take(gst_caps_to_string(caps))
    gst_mini_object_unref(caps)
    return text


cdef size_t _plane_len(size_t total, size_t offset, int stride, int rows):
    cdef size_t want = <size_t>stride * rows
    if offset >= total:
        return 0
    if offset + want > total:
        return total - offset
    return want


cdef cyview.array _view(uint8_t *data, size_t size):
    '''A buffer-protocol view of mapped memory, without a copy. Only valid
    while the memory stays mapped.'''
    cdef cyview.array arr = cyview.array(
        shape=(max(<size_t>1, size),), itemsize=1, format='B', mode='c',
        allocate_buffer=False)
    arr.data = <char *>data
    return arr


def _teardown_all():
    # Streaming threads still running at interpreter exit crash some
    # GStreamer builds; stop every pipeline first.
    for p in list(_players):
        try:
            p.teardown()
        except Exception:
            pass


atexit.register(_teardown_all)

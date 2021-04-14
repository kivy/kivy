from libcpp cimport bool
from weakref import ref
import atexit

cdef extern from 'gst/gst.h':
    ctypedef void *GstPipeline
    ctypedef void *GstElement
    ctypedef void *GstBus
    ctypedef void *GstPad
    ctypedef void *GstSample
    ctypedef void *GstBin
    ctypedef void (*appcallback_t)(void *, int, int, char *, int)
    ctypedef void (*buscallback_t)(void *, GstMessage *)
    ctypedef unsigned int guint
    ctypedef unsigned long gulong
    ctypedef void *gpointer
    ctypedef char const_gchar 'const gchar'
    ctypedef long int gint64
    ctypedef unsigned long long GstClockTime
    ctypedef int gboolean

    ctypedef enum GstState:
        GST_STATE_VOID_PENDING
        GST_STATE_NULL
        GST_STATE_READY
        GST_STATE_PAUSED
        GST_STATE_PLAYING

    ctypedef enum GstFormat:
        GST_FORMAT_TIME

    ctypedef enum GstSeekFlags:
        GST_SEEK_FLAG_KEY_UNIT
        GST_SEEK_FLAG_FLUSH

    ctypedef enum GstStateChangeReturn:
        pass

    ctypedef struct GError:
        int code
        char *message

    ctypedef enum GstMessageType:
        GST_MESSAGE_EOS
        GST_MESSAGE_ERROR
        GST_MESSAGE_WARNING
        GST_MESSAGE_INFO

    ctypedef struct GstMessage:
        GstMessageType type

    int GST_SECOND
    bool gst_init_check(int *argc, char ***argv, GError **error)
    bool gst_is_initialized()
    void gst_deinit()
    void gst_version(guint *major, guint *minor, guint *micro, guint *nano)
    GstElement *gst_element_factory_make(const_gchar *factoryname, const_gchar *name)
    bool gst_bin_add(GstBin *bin, GstElement *element)
    bool gst_bin_remove(GstBin *bin, GstElement *element)
    void gst_object_unref(void *pointer) nogil
    GstElement *gst_pipeline_new(const_gchar *name)
    void gst_bus_enable_sync_message_emission(GstBus *bus)
    GstBus *gst_pipeline_get_bus(GstPipeline *pipeline)
    GstStateChangeReturn gst_element_get_state(
            GstElement *element, GstState *state, GstState *pending,
            GstClockTime timeout) nogil
    GstStateChangeReturn gst_element_set_state(
            GstElement *element, GstState state) nogil
    void g_signal_emit_by_name(gpointer instance, const_gchar *detailed_signal,
            void *retvalue)
    void g_error_free(GError *error)
    bool gst_element_query_position(
            GstElement *element, GstFormat format, gint64 *cur) nogil
    bool gst_element_query_duration(
            GstElement *element, GstFormat format, gint64 *cur) nogil
    bool gst_element_seek_simple(
            GstElement *element, GstFormat format,
            GstSeekFlags seek_flags, gint64 seek_pos) nogil
    void gst_message_parse_error(
            GstMessage *message, GError **gerror, char **debug)
    void gst_message_parse_warning(
            GstMessage *message, GError **gerror, char **debug)
    void gst_message_parse_info(
            GstMessage *message, GError **gerror, char **debug)

cdef extern from '_gstplayer.h':
    void g_object_set_void(GstElement *element, char *name, void *value)
    void g_object_set_double(GstElement *element, char *name, double value) nogil
    void g_object_set_caps(GstElement *element, char *value)
    void g_object_set_int(GstElement *element, char *name, int value)
    gulong c_appsink_set_sample_callback(GstElement *appsink,
            appcallback_t callback, void *userdata)
    void c_appsink_pull_preroll(GstElement *appsink,
            appcallback_t callback, void *userdata) nogil
    gulong c_bus_connect_message(GstBus *bus,
            buscallback_t callback, void *userdata)
    void c_signal_disconnect(GstElement *appsink, gulong handler_id)
    void c_glib_iteration(int count)


#
# prevent gstreamer crash when some player are still working.
#

cdef list _instances = []

def _on_player_deleted(wk):
    if wk in _instances:
        _instances.remove(wk)

@atexit.register
def gst_exit_clean():
    # XXX don't use a stop() method or anything that change the state of the
    # element without releasing the GIL. Otherwise, we might have a deadlock due
    # to GIL in appsink callback + GIL already locked here.
    for wk in _instances:
        player = wk()
        if player:
            player.unload()


class GstPlayerException(Exception):
    pass


cdef void _on_appsink_sample(
        void *c_player, int width, int height,
        char *data, int datasize) with gil:
    cdef GstPlayer player = <GstPlayer>c_player
    cdef bytes buf = data[:datasize]
    if player.sample_cb:
        player.sample_cb(width, height, buf)


cdef void _on_gstplayer_message(void *c_player, GstMessage *message) with gil:
    cdef GstPlayer player = <GstPlayer>c_player
    cdef GError *err = NULL
    if message.type == GST_MESSAGE_EOS:
        player.got_eos()
    elif message.type == GST_MESSAGE_ERROR:
        gst_message_parse_error(message, &err, NULL)
        player.message_cb('error', err.message)
        g_error_free(err);
    elif message.type == GST_MESSAGE_WARNING:
        gst_message_parse_warning(message, &err, NULL)
        player.message_cb('warning', err.message)
        g_error_free(err);
    elif message.type == GST_MESSAGE_INFO:
        gst_message_parse_info(message, &err, NULL)
        player.message_cb('info', err.message)
        g_error_free(err);
    else:
        pass

def _gst_init():
    if gst_is_initialized():
        return True
    cdef int argc = 0
    cdef char **argv = NULL
    cdef GError *error
    if not gst_init_check(&argc, &argv, &error):
        msg = 'Unable to initialize gstreamer: code={} message={}'.format(
                error.code, <bytes>error.message)
        raise GstPlayerException(msg)

def get_gst_version():
    cdef unsigned int major, minor, micro, nano
    gst_version(&major, &minor, &micro, &nano)
    return (major, minor, micro, nano)


def glib_iteration(int loop):
    c_glib_iteration(loop)


cdef class GstPlayer:
    cdef GstElement *pipeline
    cdef GstElement *playbin
    cdef GstElement *appsink
    cdef GstElement *fakesink
    cdef GstBus *bus
    cdef object uri, sample_cb, eos_cb, message_cb
    cdef gulong hid_sample, hid_message
    cdef object __weakref__

    def __cinit__(self, *args, **kwargs):
        self.pipeline = self.playbin = self.appsink = self.fakesink = NULL
        self.bus = NULL
        self.hid_sample = self.hid_message = 0

    def __init__(self, uri, sample_cb=None, eos_cb=None, message_cb=None):
        super(GstPlayer, self).__init__()
        self.uri = uri
        self.sample_cb = sample_cb
        self.eos_cb = eos_cb
        self.message_cb = message_cb
        _instances.append(ref(self, _on_player_deleted))

        # ensure gstreamer is init
        _gst_init()

    def __dealloc__(self):
        self.unload()

    cdef void got_eos(self):
        if self.eos_cb:
            self.eos_cb()

    def load(self):
        cdef bytes py_uri

        # if already loaded before, clean everything.
        if self.pipeline != NULL:
            self.unload()

        # create the pipeline
        self.pipeline = gst_pipeline_new(NULL)
        if self.pipeline == NULL:
            raise GstPlayerException('Unable to create a pipeline')

        self.bus = gst_pipeline_get_bus(<GstPipeline *>self.pipeline)
        if self.bus == NULL:
            raise GstPlayerException('Unable to get the bus from the pipeline')

        gst_bus_enable_sync_message_emission(self.bus)
        if self.eos_cb or self.message_cb:
            self.hid_message = c_bus_connect_message(
                    self.bus, _on_gstplayer_message, <void *>self)

        # instantiate the playbin
        self.playbin = gst_element_factory_make('playbin', NULL)
        if self.playbin == NULL:
            raise GstPlayerException(
                'Unable to create a playbin. Consider setting the environment variable '
                'GST_REGISTRY to a user accessible path, such as ~/registry.bin')

        gst_bin_add(<GstBin *>self.pipeline, self.playbin)

        # instantiate an appsink
        if self.sample_cb:
            self.appsink = gst_element_factory_make('appsink', NULL)
            if self.appsink == NULL:
                raise GstPlayerException('Unable to create an appsink')

            g_object_set_caps(self.appsink, 'video/x-raw,format=RGB')
            g_object_set_int(self.appsink, 'max-buffers', 5)
            g_object_set_int(self.appsink, 'drop', 1)
            g_object_set_int(self.appsink, 'sync', 1)
            g_object_set_int(self.appsink, 'qos', 1)
            g_object_set_void(self.playbin, 'video-sink', self.appsink)

        else:
            self.fakesink = gst_element_factory_make('fakesink', NULL)
            if self.fakesink == NULL:
                raise GstPlayerException('Unable to create a fakesink')

            g_object_set_void(self.playbin, 'video-sink', self.fakesink)

        # configure playbin
        g_object_set_int(self.pipeline, 'async-handling', 1)
        py_uri = <bytes>self.uri.encode('utf-8')
        g_object_set_void(self.playbin, 'uri', <char *>py_uri)

        # attach the callback
        # NOTE no need to create a weakref here, as we manage to grab/release
        # the reference of self in the set_sample_callback() method.
        if self.sample_cb:
            self.hid_sample = c_appsink_set_sample_callback(
                    self.appsink, _on_appsink_sample, <void *>self)

        # get ready!
        with nogil:
            gst_element_set_state(self.pipeline, GST_STATE_READY)

    def play(self):
        if self.pipeline != NULL:
            with nogil:
                gst_element_set_state(self.pipeline, GST_STATE_PLAYING)

    def stop(self):
        if self.pipeline != NULL:
            with nogil:
                gst_element_set_state(self.pipeline, GST_STATE_NULL)
                gst_element_set_state(self.pipeline, GST_STATE_READY)

    def pause(self):
        if self.pipeline != NULL:
            with nogil:
                gst_element_set_state(self.pipeline, GST_STATE_PAUSED)

    def unload(self):
        cdef GstState current_state, pending_state

        if self.appsink != NULL and self.hid_sample != 0:
            c_signal_disconnect(self.appsink, self.hid_sample)
            self.hid_sample = 0

        if self.bus != NULL and self.hid_message != 0:
            c_signal_disconnect(<GstElement *>self.bus, self.hid_message)
            self.hid_message = 0

        if self.pipeline != NULL:
            # the state changes are async. if we want to guarantee that the
            # state is set to NULL, we need to query it. We also put a 5s
            # timeout for safety, but normally, nobody should hit it.
            with nogil:
                gst_element_set_state(self.pipeline, GST_STATE_NULL)
                gst_element_get_state(self.pipeline, &current_state,
                        &pending_state, <GstClockTime>5e9)
            gst_object_unref(self.pipeline)

        if self.bus != NULL:
            gst_object_unref(self.bus)

        self.appsink = NULL
        self.bus = NULL
        self.pipeline = NULL
        self.playbin = NULL
        self.fakesink = NULL

    def set_volume(self, float volume):
        if self.playbin != NULL:
            # XXX we need to release the GIL, on linux, you might have a race
            # condition. When running, if pulseaudio is used, it might sent a
            # message when you set the volume, in the pulse audio thread
            # The message is received by our common sync-message, and try to get
            # the GIL, and block, because here we didn't release it.
            # 1. our thread get the GIL and ask pulseaudio to set the volume
            # 2. the pulseaudio thread try to sent a message, and wait for the
            #    GIL
            with nogil:
                g_object_set_double(self.playbin, 'volume', volume)

    def get_duration(self):
        cdef double duration
        with nogil:
            duration = <double>self._get_duration()
        if duration == -1:
            return -1
        return duration / float(GST_SECOND)

    def get_position(self):
        cdef double position
        with nogil:
            position = <double>self._get_position()
        if position == -1:
            return -1
        return position / float(GST_SECOND)

    def seek(self, float percent):
        with nogil:
            self._seek(percent)

    #
    # C-like API, that doesn't require the GIL
    #

    cdef gint64 _get_duration(self) nogil:
        cdef gint64 duration = -1
        cdef GstState state
        if self.playbin == NULL:
            return -1

        # check the state
        gst_element_get_state(self.pipeline, &state, NULL,
                <GstClockTime>GST_SECOND)

        # if we are already prerolled, we can read the duration
        if state == GST_STATE_PLAYING or state == GST_STATE_PAUSED:
            gst_element_query_duration(self.playbin, GST_FORMAT_TIME, &duration)
            return duration

        # preroll
        gst_element_set_state(self.pipeline, GST_STATE_PAUSED)
        gst_element_get_state(self.pipeline, &state, NULL,
                <GstClockTime>GST_SECOND)
        gst_element_query_duration(self.playbin, GST_FORMAT_TIME, &duration)
        gst_element_set_state(self.pipeline, GST_STATE_READY)
        return duration

    cdef gint64 _get_position(self) nogil:
        cdef gint64 position = 0
        if self.playbin == NULL:
            return 0
        if not gst_element_query_position(
                self.playbin, GST_FORMAT_TIME, &position):
            return 0
        return position

    cdef void _seek(self, float percent) nogil:
        cdef GstState current_state, pending_state
        cdef gboolean ret
        cdef gint64 seek_t, duration
        if self.playbin == NULL:
            return

        duration = self._get_duration()
        if duration <= 0:
            seek_t = 0
        else:
            seek_t = <gint64>(percent * duration)
        seek_flags = GST_SEEK_FLAG_FLUSH | GST_SEEK_FLAG_KEY_UNIT
        gst_element_get_state(self.pipeline, &current_state,
                &pending_state, <GstClockTime>GST_SECOND)
        if current_state == GST_STATE_READY:
            gst_element_set_state(self.pipeline, GST_STATE_PAUSED)
        ret = gst_element_seek_simple(self.playbin, GST_FORMAT_TIME,
                <GstSeekFlags>seek_flags, seek_t)

        if not ret:
            return

        if self.appsink != NULL:
            gst_element_get_state(self.pipeline, &current_state,
                    &pending_state, <GstClockTime>GST_SECOND)
            if current_state != GST_STATE_PLAYING:
                c_appsink_pull_preroll(
                    self.appsink, _on_appsink_sample, <void *>self)

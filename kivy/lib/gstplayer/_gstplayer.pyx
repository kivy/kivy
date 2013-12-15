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
    ctypedef unsigned int guint
    ctypedef unsigned long gulong
    ctypedef void *gpointer
    ctypedef char const_gchar 'const gchar'
    ctypedef long int gint64
    ctypedef unsigned long long GstClockTime

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

    bool gst_init_check(int *argc, char ***argv, GError *error)
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
            GstElement *element, GstFormat format, gint64 *cur)
    bool gst_element_query_duration(
            GstElement *element, GstFormat format, gint64 *cur)
    bool gst_element_seek_simple(
            GstElement *element, GstFormat format,
            GstSeekFlags seek_flags, gint64 seek_pos)

cdef extern from '_gstplayer.h':
    void g_object_set_void(GstElement *element, char *name, void *value)
    void g_object_set_double(GstElement *element, char *name, double value)
    void g_object_set_caps(GstElement *element, char *value)
    void g_object_set_int(GstElement *element, char *name, int value)
    gulong c_appsink_set_sample_callback(GstElement *appsink,
            appcallback_t callback, void *userdata)
    void c_appsink_disconnect(GstElement *appsink, gulong handler_id)


#
# prevent gstreamer crash when some player are still working.
#

cdef list _instances = []

def _on_player_deleted(wk):
    if wk in _instances:
        _instances.remove(wk)

@atexit.register
def gst_exit_clean():
    for wk in _instances:
        player = wk()
        if player:
            player.stop()
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

def _gst_init():
    if gst_is_initialized():
        return True
    cdef int argc = 0
    cdef char **argv = NULL
    cdef GError error
    if not gst_init_check(&argc, &argv, &error):
        msg = 'Unable to initialize gstreamer: code={} message={}'.format(
                error.code, <bytes>error.message)
        raise GstPlayerException(msg)

def get_gst_version():
    cdef unsigned int major, minor, micro, nano
    gst_version(&major, &minor, &micro, &nano)
    return (major, minor, micro, nano)


cdef class GstPlayer:
    cdef GstElement *pipeline, *playbin, *appsink
    cdef GstBus *bus
    cdef object uri, sample_cb
    cdef gulong handler_id
    cdef object __weakref__

    def __cinit__(self, uri, sample_cb):
        self.pipeline = self.playbin = self.appsink = NULL
        self.bus = NULL
        self.handler_id = 0

    def __init__(self, uri, sample_cb):
        super(GstPlayer, self).__init__()
        self.uri = uri
        self.sample_cb = sample_cb
        _instances.append(ref(self, _on_player_deleted))

        # ensure gstreamer is init
        _gst_init()

    def __dealloc__(self):
        self.unload()

    def load(self):
        cdef char *c_uri

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

        # instanciate the playbin
        self.playbin = gst_element_factory_make('playbin', NULL)
        if self.playbin == NULL:
            raise GstPlayerException('Unable to create a playbin')

        gst_bin_add(<GstBin *>self.pipeline, self.playbin)

        # instanciate an appsink
        self.appsink = gst_element_factory_make('appsink', NULL)
        if self.appsink == NULL:
            raise GstPlayerException('Unable to create an appsink')

        g_object_set_caps(self.appsink, 'video/x-raw,format=RGB')
        g_object_set_int(self.appsink, 'max-buffers', 5)
        g_object_set_int(self.appsink, 'drop', 1)
        g_object_set_int(self.appsink, 'sync', 1)
        g_object_set_int(self.appsink, 'qos', 1)

        # configure playbin and attach appsink
        g_object_set_int(self.pipeline, 'async-handling', 1)
        g_object_set_int(self.playbin, 'buffer-duration', long(1e8))
        g_object_set_void(self.playbin, 'video-sink', self.appsink)
        c_uri = <bytes>self.uri.decode('utf-8')
        g_object_set_void(self.playbin, 'uri', c_uri)

        # attach the callback
        self.handler_id =c_appsink_set_sample_callback(
                self.appsink, _on_appsink_sample, <void *>self)

        # get ready!
        gst_element_set_state(self.pipeline, GST_STATE_READY)

    def play(self):
        if self.pipeline != NULL:
            gst_element_set_state(self.pipeline, GST_STATE_PLAYING)

    def stop(self):
        if self.pipeline != NULL:
            gst_element_set_state(self.pipeline, GST_STATE_READY)

    def pause(self):
        if self.pipeline != NULL:
            gst_element_set_state(self.pipeline, GST_STATE_PAUSED)

    def unload(self):
        cdef GstState current_state, pending_state

        if self.appsink != NULL and self.handler_id != 0:
            c_appsink_disconnect(self.appsink, self.handler_id)

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
        self.handler_id = 0

    def set_volume(self, float volume):
        if self.playbin != NULL:
            g_object_set_double(self.playbin, 'volume', volume)

    def get_duration(self):
        cdef gint64 duration = 0
        if self.playbin == NULL:
            return -1
        if not gst_element_query_duration(
                self.playbin, GST_FORMAT_TIME, &duration):
            return -1
        return duration / 1e9

    def get_position(self):
        cdef gint64 position = 0
        if self.playbin == NULL:
            return -1
        if not gst_element_query_position(
                self.playbin, GST_FORMAT_TIME, &position):
            return -1
        return position / 1e9

    def seek(self, percent):
        if self.playbin == NULL:
            return
        seek_t = percent * self.get_duration() * 1e9
        seek_flags = GST_SEEK_FLAG_FLUSH | GST_SEEK_FLAG_KEY_UNIT
        gst_element_seek_simple(self.playbin, GST_FORMAT_TIME,
                <GstSeekFlags>seek_flags, seek_t)

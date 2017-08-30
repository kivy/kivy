include "../../lib/sdl2.pxi"
include "../../include/config.pxi"

# TODO support for all platforms supported by Kivy

from kivy.core.window import Window
from kivy.core.window.window_sdl2 import WindowSDL

from libc.stdint cimport uintptr_t
from libc.stdlib cimport malloc
from libcpp cimport bool
from weakref import ref
import atexit

cdef extern from '<glib.h>':
    ctypedef int gint
    ctypedef unsigned int guint
    ctypedef unsigned long gulong
    ctypedef void *gpointer
    ctypedef char const_gchar 'const gchar'
    ctypedef long int gint64
    ctypedef long int gulong
    ctypedef int gboolean
    ctypedef void (*GDestroyNotify)(gpointer data)
    void g_print(const_gchar *format)

cdef extern from '<glib-object.h>':
    ctypedef void *GValue
    ctypedef void *GCallback
    
    gulong g_signal_connect(gpointer *instance, const_gchar *detailed_signal, GCallback *c_handler, void *data)
    void g_signal_emit_by_name(gpointer *instance, const_gchar *detailed_signal, gpointer *param)
    gint g_value_get_int(GValue *value)

cdef extern from 'gst/gst.h':
    ctypedef void *GstPipeline
    ctypedef void *GstBin
    ctypedef void *GstElement
    ctypedef void *GstBus
    ctypedef void *GstPad
    ctypedef void *GstSample
    ctypedef void *GstBuffer
    ctypedef void *GstCaps
    ctypedef void *GstStructure
    ctypedef void (*appcallback_t)(void *, int, int, char *, int)
    ctypedef void (*buscallback_t)(void *, GstMessage *)
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

    ctypedef enum GstMessageType:
        GST_MESSAGE_EOS
        GST_MESSAGE_ERROR
        GST_MESSAGE_WARNING
        GST_MESSAGE_INFO

    ctypedef enum GstFlowReturn:
        GST_FLOW_CUSTOM_SUCCESS_1
        GST_FLOW_CUTSOM_SUCCESS_2
        GST_FLOW_CUTSOM_SUCCESS
        GST_FLOW_OK
        GST_FLOW_NOT_LINKED
        GST_FLOW_FLUSHING
        GST_FLOW_EOS
        GST_FLOW_NOT_NEGOTIATED
        GST_FLOW_ERROR
        GST_FLOW_NOT_SUPPORTED
        GST_FLOW_CUSTOM_ERROR
        GST_FLOW_CUSTOM_ERROR_1
        GST_FLOW_CUSTOM_ERROR_2

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
    GstBuffer *gst_sample_get_buffer(GstSample *sample)
    GstCaps *gst_sample_get_caps(GstSample *sample)
    GstStructure *gst_caps_get_structure(GstCaps *caps, guint index)
    GValue *gst_structure_get_value(GstStructure *struct, const_gchar *prop)
    gboolean gst_element_link(GstElement *src, GstElement *target)
    GstPad *gst_element_get_static_pad(GstElement *element, const_gchar *pad)
    GstPad *gst_ghost_pad_new(const_gchar *name, GstPad *target)
    gboolean gst_pad_set_active(GstPad *pad, gboolean active)
    gboolean gst_element_add_pad(GstElement *element, GstPad *pad)
    GstElement *gst_bin_new(const_gchar *name)
    void gst_bin_add_many(GstBin *bin, GstElement *element_2, GstElement *element_2, void *null)
    
cdef extern from '<gst/app/gstappsink.h>':
    ctypedef void *GstAppSink
    ctypedef struct GstAppSinkCallbacks:
        void (*eos)(GstAppSink *appsink, gpointer user_data)
        GstFlowReturn (*new_preroll)(GstAppSink *appsink, gpointer user_data)
        GstFlowReturn (*new_sample)(GstAppSink *appsink, gpointer user_data)

    GstSample* gst_app_sink_pull_preroll (GstAppSink *appsink)
    GstSample* gst_app_sink_pull_sample (GstAppSink *appsink)
    void gst_app_sink_set_callbacks(GstAppSink *appsink,
        GstAppSinkCallbacks *callbacks, gpointer user_data, GDestroyNotify notify)

DEF GST_USE_UNSTABLE_API = 1
    
cdef extern from '_gstgl.h':
    void gst_gl_init (SDL_Window *window)
    void gst_gl_set_bus_cb (GstBus *bus)
    void gst_gl_stop_pipeline (GstPipeline *pipeline) nogil
    
    guint get_texture_id_from_buffer (GstBuffer *buf, guint width, guint height)

cdef extern from '_gstglplayer.h':
    void g_object_set_void(GstElement *element, char *name, void *value)
    void g_object_set_double(GstElement *element, char *name, double value) nogil
    void g_object_set_caps(GstElement *element, char *value)
    void g_object_set_int(GstElement *element, char *name, int value)
    void dump_dot_file(GstPipeline *pipeline, const_gchar *filename)
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

cdef void _on_appsink_destroyed(gpointer data):
    # appsink destroyed. i don't know what this callback is supposed to do.
    pass

cdef void _on_appsink_eos(GstAppSink *appsink, void *user_data):
    g_print('on_appsink_eos')
    cdef GstGLPlayer player = <object>user_data
    if player.eos_cb:
        player.eos_cb()        

cdef GstFlowReturn _on_appsink_preroll(GstAppSink *appsink, void *user_data):
    g_print('on_appsink_preroll')
    cdef GstGLPlayer player = <object>user_data
    cdef GstSample *sample
    
    sample = gst_app_sink_pull_preroll(appsink)
    if sample: player.process_sample(sample)            

    return GST_FLOW_OK

cdef GstFlowReturn _on_appsink_sample(GstAppSink *appsink, void *user_data):
    g_print('on_appsink_sample')
    cdef GstGLPlayer player = <object>user_data
    cdef GstSample *sample
    
    sample = gst_app_sink_pull_sample(appsink)
    if sample: player.process_sample(sample)            

    return GST_FLOW_OK

class GstGLPlayerException(Exception):
    pass

cdef void _on_gstplayer_message(void *c_player, GstMessage *message) with gil:
    cdef GstGLPlayer player = <GstGLPlayer>c_player
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
        raise GstGLPlayerException(msg)

def get_gst_version():
    cdef unsigned int major, minor, micro, nano
    gst_version(&major, &minor, &micro, &nano)
    return (major, minor, micro, nano)


def glib_iteration(int loop):
    c_glib_iteration(loop)


cdef class GstGLPlayer:
    cdef GstElement *pipeline
    cdef GstElement *playbin
    cdef GstElement *outbin
    cdef GstElement *glupload
    cdef GstElement *appsink
    cdef GstElement *fakesink
    cdef GstBus *bus    

    cdef object uri, eos_cb, texture_cb, message_cb
    cdef object kivy_window
    cdef gulong hid_sample, hid_message
    cdef object __weakref__

    def __cinit__(self, *args, **kwargs):
        self.pipeline = self.playbin = self.appsink = self.outbin = self.glupload = self.fakesink = NULL
        self.bus = NULL

    def __init__(self, uri, texture_cb=None, eos_cb=None, message_cb=None):    
        super(GstGLPlayer, self).__init__()
        self.uri = uri
        self.texture_cb = texture_cb
        self.eos_cb = eos_cb
        self.message_cb = message_cb
        _instances.append(ref(self, _on_player_deleted))

        # ensure gstreamer is init
        _gst_init()

        if not type(Window) == WindowSDL:
            raise GstGLPlayerException('Window is not using SDL2 provider.')
        
        self.gst_gl_init()
    
    cdef void gst_gl_init(self):
        cdef uintptr_t sdl_window_pointer
        sdl_window_pointer = Window.get_sdl2_window_pointer()
        gst_gl_init(<SDL_Window *>sdl_window_pointer)

    def __dealloc__(self):
        self.unload()

    cdef void got_eos(self):
        if self.eos_cb:
            self.eos_cb()

    def load(self):
        cdef bytes py_uri
        cdef GstPad *sinkpad
        cdef GstPad *ghost_sinkpad
        cdef GstAppSinkCallbacks *callbacks = <GstAppSinkCallbacks *>malloc(sizeof(GstAppSinkCallbacks))
                
        # if already loaded before, clean everything.
        if self.pipeline != NULL:
            self.unload()

        # create the pipeline
        self.pipeline = gst_pipeline_new(NULL)
        if self.pipeline == NULL:
            raise GstGLPlayerException('Unable to create a pipeline')

        self.bus = gst_pipeline_get_bus(<GstPipeline *>self.pipeline)
        if self.bus == NULL:
            raise GstGLPlayerException('Unable to get the bus from the pipeline')

        gst_bus_enable_sync_message_emission(self.bus)
        if self.eos_cb or self.message_cb:
            self.hid_message = c_bus_connect_message(
                    self.bus, _on_gstplayer_message, <void *>self)
        
        gst_gl_set_bus_cb(self.bus);

        # instantiate the playbin
        self.playbin = gst_element_factory_make('playbin', NULL)
        if self.playbin == NULL:
            raise GstGLPlayerException('Unable to create a playbin')

        gst_bin_add(<GstBin *>self.pipeline, self.playbin)

        # instantiate a glupload and an appsink, put them in a bin
        if self.texture_cb:
            self.glupload = gst_element_factory_make('glupload', NULL)
            if self.glupload == NULL:
                raise GstGLPlayerException('Unable to create a glupload')

            self.appsink = gst_element_factory_make('appsink', NULL)
            if self.appsink == NULL:
                raise GstGLPlayerException('Unable to create an appsink')

            g_object_set_caps(self.appsink, 'video/x-raw(memory:GLMemory), format=RGBA')
            g_object_set_int(self.appsink, 'max-buffers', 5)
            g_object_set_int(self.appsink, 'drop', 1)
            g_object_set_int(self.appsink, 'sync', 1)
            g_object_set_int(self.appsink, 'qos', 1)
            
            self.outbin = gst_bin_new('outbin')
            gst_bin_add_many(<GstBin *>self.outbin, self.glupload, self.appsink, NULL);

            if not gst_element_link(self.glupload, self.appsink):
                raise GstGLPlayerException('Could not link glupload and appsink')
            
            sinkpad = gst_element_get_static_pad(self.glupload, 'sink')
            ghost_sinkpad = gst_ghost_pad_new('sink', sinkpad)
            gst_pad_set_active(ghost_sinkpad, <gboolean>True)
            gst_element_add_pad(self.outbin, ghost_sinkpad)

            g_object_set_void(self.playbin, 'video-sink', self.outbin)

        else:
            self.fakesink = gst_element_factory_make('fakesink', NULL)
            if self.fakesink == NULL:
                raise GstGLPlayerException('Unable to create a fakesink')

            g_object_set_void(self.playbin, 'video-sink', self.fakesink)

        # configure playbin
        g_object_set_int(self.pipeline, 'async-handling', 1)
        py_uri = <bytes>self.uri.encode('utf-8')
        g_object_set_void(self.playbin, 'uri', <char *>py_uri)

        # attach the callback
        if self.texture_cb:
            callbacks.eos = &_on_appsink_eos
            callbacks.new_preroll = &_on_appsink_preroll
            callbacks.new_sample = &_on_appsink_sample
            
            gst_app_sink_set_callbacks(<GstAppSink *>self.appsink, callbacks, <void *>self, <GDestroyNotify>_on_appsink_destroyed)

        # get ready!
        with nogil:
            gst_element_set_state(self.pipeline, GST_STATE_READY)
    
    cdef void process_sample(self, GstSample *sample) with gil:
        cdef GstBuffer *buf
        cdef GstCaps *caps
        cdef GstStructure *struct
        
        if self.texture_cb:
            caps = gst_sample_get_caps(sample)
            struct = gst_caps_get_structure(caps, 0)
            width = g_value_get_int(gst_structure_get_value(struct, 'width'))
            height = g_value_get_int(gst_structure_get_value(struct, 'height'))
        
            buf = gst_sample_get_buffer(sample)
            texture = get_texture_id_from_buffer(buf, width, height)
            
            self.texture_cb(width, height, texture)
        
    def play(self):
        if self.pipeline != NULL:
            with nogil:
                gst_element_set_state(self.pipeline, GST_STATE_PLAYING)
            
            dump_dot_file(self.pipeline, 'gstgl_pipeline')
            dump_dot_file(self.outbin, 'gstgl_outbin')

    def stop(self):
        if self.pipeline != NULL:
            with nogil:
                gst_gl_stop_pipeline(self.pipeline)
                gst_element_set_state(self.pipeline, GST_STATE_READY)

    def pause(self):
        if self.pipeline != NULL:
            with nogil:
                gst_element_set_state(self.pipeline, GST_STATE_PAUSED)

    def unload(self):
        cdef GstState current_state, pending_state

        if self.bus != NULL and self.hid_message != 0:
            c_signal_disconnect(<GstElement *>self.bus, self.hid_message)
            self.hid_message = 0

        if self.pipeline != NULL:
            # the state changes are async. if we want to guarantee that the
            # state is set to NULL, we need to query it. We also put a 5s
            # timeout for safety, but normally, nobody should hit it.
            with nogil:
                gst_gl_stop_pipeline(self.pipeline)
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
        cdef float duration
        with nogil:
            duration = self._get_duration()
        if duration == -1:
            return -1
        return duration / float(GST_SECOND)

    def get_position(self):
        cdef float position
        with nogil:
            position = self._get_position()
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

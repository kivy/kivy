/*
 * Runtime loader for the part of the GStreamer C API that
 * kivy.lib.gstplayer uses.
 *
 * Kivy builds this module with no GStreamer headers or libraries: the
 * libraries are opened when the module is imported (dlopen() on Linux,
 * LoadLibraryExW() on Windows) and every function is called through the
 * kgst_api table below. Only GStreamer's stable 1.x C ABI is used, and
 * only four small public structs are mirrored (GError, GstMapInfo, the
 * head of GstMessage and the head of GstVideoMeta). _gstplayer.pyx checks
 * the mirrored GstMessage layout once GStreamer is initialized.
 *
 * Header-only: it is included by _gstplayer.pyx, the only user.
 */
#ifndef KIVY_GST_LOADER_H
#define KIVY_GST_LOADER_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#ifdef _WIN32
#  ifndef WIN32_LEAN_AND_MEAN
#    define WIN32_LEAN_AND_MEAN
#  endif
#  include <windows.h>
#else
#  include <dlfcn.h>
#endif

/* ---- GLib / GStreamer scalar types (matching their public typedefs) ---- */

typedef int kgboolean;
typedef unsigned int kguint;
typedef uint32_t kGQuark;
typedef size_t kGType;

typedef struct {
    kGQuark domain;
    int code;
    char *message;
} kGError;

/* Opaque objects. */
typedef struct _kGstElement kGstElement;
typedef struct _kGstObject kGstObject;
typedef struct _kGstBus kGstBus;
typedef struct _kGstCaps kGstCaps;
typedef struct _kGstStructure kGstStructure;
typedef struct _kGstSample kGstSample;
typedef struct _kGstBuffer kGstBuffer;
typedef struct _kGstMemory kGstMemory;
typedef struct _kGstContext kGstContext;
typedef struct _kGstPad kGstPad;
typedef struct _kGstIterator kGstIterator;
typedef struct _kGstElementFactory kGstElementFactory;
typedef struct _kGstGLDisplay kGstGLDisplay;
typedef struct _kGstGLContext kGstGLContext;

/* GValue: a GType followed by two 64-bit data words. Only used as an
 * out-parameter for gst_iterator_next() and read with g_value_get_object. */
typedef struct {
    kGType g_type;
    uint64_t data[2];
} kGValue;

/* GstMiniObject, as in gstminiobject.h (1.0 to 1.28). */
typedef struct {
    kGType type;
    int refcount;
    int lockstate;
    unsigned int flags;
    void *copy;
    void *dispose;
    void *free;
    unsigned int priv_uint;
    void *priv_pointer;
} kGstMiniObject;

/* The public head of GstMessage (gstmessage.h). The type is an enum whose
 * extended values set bit 31, so it is read as unsigned. */
typedef struct {
    kGstMiniObject mini_object;
    unsigned int type;
    uint64_t timestamp;
    kGstObject *src;
    uint32_t seqnum;
} kGstMessage;

/* GstMapInfo (gstmemory.h). */
typedef struct {
    kGstMemory *memory;
    int flags;
    uint8_t *data;
    size_t size;
    size_t maxsize;
    void *user_data[4];
    void *_gst_reserved[4];
} kGstMapInfo;

/* The public head of GstVideoMeta (gstvideometa.h). */
typedef struct {
    int flags;
    const void *info;
} kGstMeta;

typedef struct {
    kGstMeta meta;
    kGstBuffer *buffer;
    int flags;
    int format;
    int id;
    unsigned int width;
    unsigned int height;
    unsigned int n_planes;
    size_t offset[4];
    int stride[4];
} kGstVideoMeta;

/* ---- Libraries ---- */

enum {
    KGST_LIB_GLIB = 0,
    KGST_LIB_GOBJECT,
    KGST_LIB_GST,
    KGST_LIB_GSTAPP,
    KGST_LIB_GSTVIDEO,
    KGST_LIB_GSTPBUTILS,
    KGST_LIB_GSTGL,
    KGST_LIB_COUNT
};

/* ---- The function table ----
 *
 * X(library, required, return type, name, parameters)
 *
 * A required function missing from its library fails the load. Optional
 * ones are left NULL; the Cython side checks before calling them.
 */
#define KGST_FUNCTIONS(X) \
    X(KGST_LIB_GLIB, 1, void, g_free, (void *mem)) \
    X(KGST_LIB_GLIB, 1, void, g_error_free, (kGError *error)) \
    X(KGST_LIB_GOBJECT, 1, void, g_object_set, (void *object, const char *first_property_name, ...)) \
    X(KGST_LIB_GOBJECT, 1, void, g_object_get, (void *object, const char *first_property_name, ...)) \
    X(KGST_LIB_GOBJECT, 1, void *, g_value_get_object, (const kGValue *value)) \
    X(KGST_LIB_GOBJECT, 1, void, g_value_unset, (kGValue *value)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_init_check, (int *argc, char ***argv, kGError **error)) \
    X(KGST_LIB_GST, 1, void, gst_version, (kguint *major, kguint *minor, kguint *micro, kguint *nano)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_is_initialized, (void)) \
    X(KGST_LIB_GST, 1, kGstElement *, gst_element_factory_make, (const char *factoryname, const char *name)) \
    X(KGST_LIB_GST, 1, kGstElementFactory *, gst_element_factory_find, (const char *name)) \
    X(KGST_LIB_GST, 1, const char *, gst_element_factory_get_metadata, (kGstElementFactory *factory, const char *key)) \
    X(KGST_LIB_GST, 1, kGstElementFactory *, gst_element_get_factory, (kGstElement *element)) \
    X(KGST_LIB_GST, 1, int, gst_element_set_state, (kGstElement *element, int state)) \
    X(KGST_LIB_GST, 1, int, gst_element_get_state, (kGstElement *element, int *state, int *pending, uint64_t timeout)) \
    X(KGST_LIB_GST, 1, kGstBus *, gst_element_get_bus, (kGstElement *element)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_element_query_position, (kGstElement *element, int format, int64_t *cur)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_element_query_duration, (kGstElement *element, int format, int64_t *duration)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_element_seek_simple, (kGstElement *element, int format, int seek_flags, int64_t seek_pos)) \
    X(KGST_LIB_GST, 1, void, gst_element_set_context, (kGstElement *element, kGstContext *context)) \
    X(KGST_LIB_GST, 1, kGstPad *, gst_element_get_static_pad, (kGstElement *element, const char *name)) \
    X(KGST_LIB_GST, 1, kGstCaps *, gst_pad_get_current_caps, (kGstPad *pad)) \
    X(KGST_LIB_GST, 1, kGstElement *, gst_bin_get_by_name, (kGstElement *bin, const char *name)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_bin_recalculate_latency, (kGstElement *bin)) \
    X(KGST_LIB_GST, 1, kGstIterator *, gst_bin_iterate_recurse, (kGstElement *bin)) \
    X(KGST_LIB_GST, 1, int, gst_iterator_next, (kGstIterator *it, kGValue *elem)) \
    X(KGST_LIB_GST, 1, void, gst_iterator_free, (kGstIterator *it)) \
    X(KGST_LIB_GST, 1, kGstElement *, gst_parse_launch, (const char *pipeline_description, kGError **error)) \
    X(KGST_LIB_GST, 1, kGstElement *, gst_parse_bin_from_description, (const char *bin_description, kgboolean ghost_unlinked_pads, kGError **err)) \
    X(KGST_LIB_GST, 1, kGstMessage *, gst_bus_pop, (kGstBus *bus)) \
    X(KGST_LIB_GST, 1, void, gst_message_parse_error, (kGstMessage *message, kGError **gerror, char **debug)) \
    X(KGST_LIB_GST, 1, void, gst_message_parse_warning, (kGstMessage *message, kGError **gerror, char **debug)) \
    X(KGST_LIB_GST, 1, void, gst_message_parse_error_details, (kGstMessage *message, const kGstStructure **structure)) \
    X(KGST_LIB_GST, 1, void, gst_message_parse_buffering, (kGstMessage *message, int *percent)) \
    X(KGST_LIB_GST, 1, void, gst_message_parse_state_changed, (kGstMessage *message, int *oldstate, int *newstate, int *pending)) \
    X(KGST_LIB_GST, 1, const kGstStructure *, gst_message_get_structure, (kGstMessage *message)) \
    X(KGST_LIB_GST, 1, void, gst_message_parse_tag, (kGstMessage *message, void **tag_list)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_tag_list_get_string, (const void *list, const char *tag, char **value)) \
    X(KGST_LIB_GST, 1, kGstMessage *, gst_message_new_eos, (kGstObject *src)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_structure_has_name, (const kGstStructure *structure, const char *name)) \
    X(KGST_LIB_GST, 1, const char *, gst_structure_get_string, (const kGstStructure *structure, const char *fieldname)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_structure_get_int, (const kGstStructure *structure, const char *fieldname, int *value)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_structure_get_uint, (const kGstStructure *structure, const char *fieldname, kguint *value)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_structure_get_fraction, (const kGstStructure *structure, const char *fieldname, int *num, int *den)) \
    X(KGST_LIB_GST, 1, void, gst_structure_set, (kGstStructure *structure, const char *fieldname, ...)) \
    X(KGST_LIB_GST, 1, void, gst_mini_object_unref, (void *mini_object)) \
    X(KGST_LIB_GST, 1, void *, gst_object_ref_sink, (void *object)) \
    X(KGST_LIB_GST, 1, void, gst_object_unref, (void *object)) \
    X(KGST_LIB_GST, 1, char *, gst_object_get_name, (kGstObject *object)) \
    X(KGST_LIB_GST, 1, char *, gst_caps_to_string, (const kGstCaps *caps)) \
    X(KGST_LIB_GST, 1, kGstStructure *, gst_caps_get_structure, (const kGstCaps *caps, kguint index)) \
    X(KGST_LIB_GST, 1, kGstBuffer *, gst_sample_get_buffer, (kGstSample *sample)) \
    X(KGST_LIB_GST, 1, kGstCaps *, gst_sample_get_caps, (kGstSample *sample)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_buffer_map, (kGstBuffer *buffer, kGstMapInfo *info, int flags)) \
    X(KGST_LIB_GST, 1, void, gst_buffer_unmap, (kGstBuffer *buffer, kGstMapInfo *info)) \
    X(KGST_LIB_GST, 1, kguint, gst_buffer_n_memory, (kGstBuffer *buffer)) \
    X(KGST_LIB_GST, 1, kGstMemory *, gst_buffer_peek_memory, (kGstBuffer *buffer, kguint idx)) \
    X(KGST_LIB_GST, 1, void *, gst_buffer_get_meta, (kGstBuffer *buffer, kGType api)) \
    X(KGST_LIB_GST, 1, kgboolean, gst_memory_map, (kGstMemory *mem, kGstMapInfo *info, int flags)) \
    X(KGST_LIB_GST, 1, void, gst_memory_unmap, (kGstMemory *mem, kGstMapInfo *info)) \
    X(KGST_LIB_GST, 1, char *, gst_filename_to_uri, (const char *filename, kGError **error)) \
    X(KGST_LIB_GST, 1, kGQuark, gst_core_error_quark, (void)) \
    X(KGST_LIB_GST, 1, kGQuark, gst_stream_error_quark, (void)) \
    X(KGST_LIB_GST, 1, kGQuark, gst_resource_error_quark, (void)) \
    X(KGST_LIB_GST, 1, kGstContext *, gst_context_new, (const char *context_type, kgboolean persistent)) \
    X(KGST_LIB_GST, 1, kGstStructure *, gst_context_writable_structure, (kGstContext *context)) \
    X(KGST_LIB_GSTAPP, 1, kGstSample *, gst_app_sink_try_pull_sample, (kGstElement *appsink, uint64_t timeout)) \
    X(KGST_LIB_GSTAPP, 1, kGstSample *, gst_app_sink_try_pull_preroll, (kGstElement *appsink, uint64_t timeout)) \
    X(KGST_LIB_GSTVIDEO, 1, kGType, gst_video_meta_api_get_type, (void)) \
    X(KGST_LIB_GSTPBUTILS, 0, void, gst_pb_utils_init, (void)) \
    X(KGST_LIB_GSTPBUTILS, 0, kgboolean, gst_is_missing_plugin_message, (kGstMessage *msg)) \
    X(KGST_LIB_GSTPBUTILS, 0, char *, gst_missing_plugin_message_get_description, (kGstMessage *msg)) \
    X(KGST_LIB_GSTGL, 0, kGstGLDisplay *, gst_gl_display_new, (void)) \
    X(KGST_LIB_GSTGL, 0, kGstGLDisplay *, gst_gl_display_egl_new_with_egl_display, (void *display)) \
    X(KGST_LIB_GSTGL, 0, kGstGLDisplay *, gst_gl_display_x11_new_with_display, (void *display)) \
    X(KGST_LIB_GSTGL, 0, kgboolean, gst_gl_display_ensure_context, (kGstGLDisplay *display, kGstGLContext *other_context, kGstGLContext **context, kGError **error)) \
    X(KGST_LIB_GSTGL, 0, kGstGLContext *, gst_gl_context_new_wrapped, (kGstGLDisplay *display, uintptr_t handle, int context_type, int available_apis)) \
    X(KGST_LIB_GSTGL, 0, kgboolean, gst_gl_context_activate, (kGstGLContext *context, kgboolean activate)) \
    X(KGST_LIB_GSTGL, 0, kgboolean, gst_gl_context_fill_info, (kGstGLContext *context, kGError **error)) \
    X(KGST_LIB_GSTGL, 0, kGType, gst_gl_context_get_type, (void)) \
    X(KGST_LIB_GSTGL, 0, void, gst_context_set_gl_display, (kGstContext *context, kGstGLDisplay *display)) \
    X(KGST_LIB_GSTGL, 0, int, gst_gl_platform_from_string, (const char *platform_s)) \
    X(KGST_LIB_GSTGL, 0, int, gst_gl_api_from_string, (const char *api_s)) \
    X(KGST_LIB_GSTGL, 0, kGType, gst_gl_sync_meta_api_get_type, (void)) \
    X(KGST_LIB_GSTGL, 0, void, gst_gl_sync_meta_wait, (void *sync_meta, kGstGLContext *context)) \
    X(KGST_LIB_GSTGL, 0, kgboolean, gst_is_gl_memory, (kGstMemory *mem))

#define KGST_MEMBER(lib, req, ret, name, args) ret (*name) args;
typedef struct {
    KGST_FUNCTIONS(KGST_MEMBER)
} kgst_api_t;
#undef KGST_MEMBER

static kgst_api_t kgst_api;
static void *kgst_libs[KGST_LIB_COUNT];

/* Library file names: Linux sonames; Windows MSVC names first, then MinGW. */
#ifdef _WIN32
static const char *kgst_lib_names[KGST_LIB_COUNT][2] = {
    {"glib-2.0-0.dll", "libglib-2.0-0.dll"},
    {"gobject-2.0-0.dll", "libgobject-2.0-0.dll"},
    {"gstreamer-1.0-0.dll", "libgstreamer-1.0-0.dll"},
    {"gstapp-1.0-0.dll", "libgstapp-1.0-0.dll"},
    {"gstvideo-1.0-0.dll", "libgstvideo-1.0-0.dll"},
    {"gstpbutils-1.0-0.dll", "libgstpbutils-1.0-0.dll"},
    {"gstgl-1.0-0.dll", "libgstgl-1.0-0.dll"},
};
#else
static const char *kgst_lib_names[KGST_LIB_COUNT][2] = {
    {"libglib-2.0.so.0", NULL},
    {"libgobject-2.0.so.0", NULL},
    {"libgstreamer-1.0.so.0", NULL},
    {"libgstapp-1.0.so.0", NULL},
    {"libgstvideo-1.0.so.0", NULL},
    {"libgstpbutils-1.0.so.0", NULL},
    {"libgstgl-1.0.so.0", NULL},
};
#endif

/* Libraries that may be missing: no pbutils means generic missing-plugin
 * text, no GL means no shared-texture path. */
static const int kgst_lib_optional[KGST_LIB_COUNT] = {0, 0, 0, 0, 0, 1, 1};

/* The path each library was opened from, for the log line. */
static char kgst_gst_path[1024];

static void *kgst_open_one(const char *dir, const char *name)
{
#ifdef _WIN32
    wchar_t wpath[MAX_PATH * 2];
    char path[MAX_PATH * 2];
    DWORD flags;
    HMODULE h;
    if (dir && dir[0]) {
        snprintf(path, sizeof(path), "%s\\%s", dir, name);
        flags = LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS;
    } else {
        snprintf(path, sizeof(path), "%s", name);
        flags = 0;
    }
    if (!MultiByteToWideChar(CP_UTF8, 0, path, -1, wpath, MAX_PATH * 2))
        return NULL;
    h = LoadLibraryExW(wpath, NULL, flags);
    return (void *)h;
#else
    char path[4096];
    if (dir && dir[0])
        snprintf(path, sizeof(path), "%s/%s", dir, name);
    else
        snprintf(path, sizeof(path), "%s", name);
    return dlopen(path, RTLD_NOW | RTLD_LOCAL);
#endif
}

static void *kgst_sym(void *lib, const char *name)
{
    if (!lib)
        return NULL;
#ifdef _WIN32
    return (void *)GetProcAddress((HMODULE)lib, name);
#else
    return dlsym(lib, name);
#endif
}

static void kgst_last_os_error(char *buf, size_t n)
{
#ifdef _WIN32
    snprintf(buf, n, "error %lu", (unsigned long)GetLastError());
#else
    const char *e = dlerror();
    snprintf(buf, n, "%s", e ? e : "unknown error");
#endif
}

static void kgst_record_path(void *lib)
{
#ifdef _WIN32
    wchar_t wbuf[1024];
    DWORD n = GetModuleFileNameW((HMODULE)lib, wbuf, 1024);
    if (n > 0 && n < 1024)
        WideCharToMultiByte(CP_UTF8, 0, wbuf, -1, kgst_gst_path,
                            sizeof(kgst_gst_path), NULL, NULL);
#else
    void *sym = dlsym(lib, "gst_init_check");
    Dl_info info;
    if (sym && dladdr(sym, &info) && info.dli_fname)
        snprintf(kgst_gst_path, sizeof(kgst_gst_path), "%s", info.dli_fname);
#endif
}

/* Open the libraries and fill kgst_api. `dir` is the directory holding
 * libgstreamer, or NULL/"" for the platform's normal search. Returns 0 on
 * success, -1 with a message in `err` otherwise. Calling it again after a
 * success is a no-op. */
static int kgst_load(const char *dir, char *err, size_t errlen)
{
    static int loaded = 0;
    int i, j;
    char oserr[512];
    if (loaded)
        return 0;
    for (i = 0; i < KGST_LIB_COUNT; i++) {
        kgst_libs[i] = NULL;
        for (j = 0; j < 2 && !kgst_libs[i]; j++) {
            if (!kgst_lib_names[i][j])
                continue;
            kgst_libs[i] = kgst_open_one(dir, kgst_lib_names[i][j]);
        }
        if (!kgst_libs[i] && !kgst_lib_optional[i]) {
            kgst_last_os_error(oserr, sizeof(oserr));
            snprintf(err, errlen, "cannot open %s%s%s: %s",
                     (dir && dir[0]) ? dir : "",
                     (dir && dir[0]) ? "/" : "",
                     kgst_lib_names[i][0], oserr);
            return -1;
        }
    }
    kgst_record_path(kgst_libs[KGST_LIB_GST]);

#define KGST_RESOLVE(lib, req, ret, name, args) \
    *(void **)(&kgst_api.name) = kgst_sym(kgst_libs[lib], #name); \
    if (req && !kgst_api.name) { \
        snprintf(err, errlen, "symbol %s not found in %s", #name, \
                 kgst_lib_names[lib][0]); \
        return -1; \
    }
    KGST_FUNCTIONS(KGST_RESOLVE)
#undef KGST_RESOLVE

    loaded = 1;
    return 0;
}

static int kgst_have_lib(int lib)
{
    return lib >= 0 && lib < KGST_LIB_COUNT && kgst_libs[lib] != NULL;
}

static const char *kgst_loaded_path(void)
{
    return kgst_gst_path;
}

/* ---- Kivy's current GL context, read from the GL platform itself ---- */

enum {
    KGST_GLP_NONE = 0,
    KGST_GLP_EGL = 1,
    KGST_GLP_GLX = 2,
    KGST_GLP_WGL = 3
};

typedef void *(*kgst_noarg_ptr_fn)(void);

#ifdef _WIN32
typedef BOOL (WINAPI *kgst_wglMakeCurrent_fn)(HDC, HGLRC);
#endif

/* Returns the platform of the GL context current on the calling thread and
 * fills `ctx` and `dpy` (EGLDisplay, X11 Display* or the WGL HDC). Only
 * libraries the process has already loaded are looked at. */
static int kgst_gl_current(void **ctx, void **dpy)
{
    kgst_noarg_ptr_fn get_ctx, get_dpy;
    *ctx = NULL;
    *dpy = NULL;
#ifdef _WIN32
    HMODULE h = GetModuleHandleA("opengl32.dll");
    if (h) {
        get_ctx = (kgst_noarg_ptr_fn)GetProcAddress(h, "wglGetCurrentContext");
        get_dpy = (kgst_noarg_ptr_fn)GetProcAddress(h, "wglGetCurrentDC");
        if (get_ctx && get_dpy && (*ctx = get_ctx()) != NULL) {
            *dpy = get_dpy();
            return KGST_GLP_WGL;
        }
    }
    h = GetModuleHandleA("libEGL.dll");
    if (h) {
        get_ctx = (kgst_noarg_ptr_fn)GetProcAddress(h, "eglGetCurrentContext");
        get_dpy = (kgst_noarg_ptr_fn)GetProcAddress(h, "eglGetCurrentDisplay");
        if (get_ctx && get_dpy && (*ctx = get_ctx()) != NULL) {
            *dpy = get_dpy();
            return KGST_GLP_EGL;
        }
    }
    return KGST_GLP_NONE;
#else
    static const char *egl_names[] = {"libEGL.so.1", "libEGL.so", NULL};
    static const char *glx_names[] = {"libGLX.so.0", "libGL.so.1", "libGL.so", NULL};
    void *h;
    int i;
    for (i = 0; egl_names[i]; i++) {
        h = dlopen(egl_names[i], RTLD_LAZY | RTLD_NOLOAD);
        if (!h)
            continue;
        get_ctx = (kgst_noarg_ptr_fn)dlsym(h, "eglGetCurrentContext");
        get_dpy = (kgst_noarg_ptr_fn)dlsym(h, "eglGetCurrentDisplay");
        if (get_ctx && get_dpy && (*ctx = get_ctx()) != NULL) {
            *dpy = get_dpy();
            dlclose(h);
            return KGST_GLP_EGL;
        }
        dlclose(h);
    }
    for (i = 0; glx_names[i]; i++) {
        h = dlopen(glx_names[i], RTLD_LAZY | RTLD_NOLOAD);
        if (!h)
            continue;
        get_ctx = (kgst_noarg_ptr_fn)dlsym(h, "glXGetCurrentContext");
        get_dpy = (kgst_noarg_ptr_fn)dlsym(h, "glXGetCurrentDisplay");
        if (get_ctx && get_dpy && (*ctx = get_ctx()) != NULL) {
            *dpy = get_dpy();
            dlclose(h);
            return KGST_GLP_GLX;
        }
        dlclose(h);
    }
    return KGST_GLP_NONE;
#endif
}

/* WGL only: make `ctx` current on `dc` (both NULL releases the current
 * context). Returns 1 on success. Elsewhere it does nothing. */
static int kgst_wgl_make_current(void *dc, void *ctx)
{
#ifdef _WIN32
    HMODULE h = GetModuleHandleA("opengl32.dll");
    kgst_wglMakeCurrent_fn fn;
    if (!h)
        return 0;
    fn = (kgst_wglMakeCurrent_fn)GetProcAddress(h, "wglMakeCurrent");
    return fn ? (int)fn((HDC)dc, (HGLRC)ctx) : 0;
#else
    (void)dc;
    (void)ctx;
    return 0;
#endif
}

#endif /* KIVY_GST_LOADER_H */

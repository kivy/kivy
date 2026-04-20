# cython: language_level=3
"""
Minimal Cython declarations for the ThorVG v1.0.4 C API (``thorvg_capi.h``).

Only the surface required by Kivy's SVG, SVG-image and Lottie providers is
declared here. See [kivy/lib/thorvg/_thorvg.pyx](_thorvg.pyx) for the wrapper
implementation and the public Python surface in
[kivy/lib/thorvg/__init__.py](__init__.py).
"""

from libc.stdint cimport uint8_t, uint16_t, uint32_t, int32_t
from libcpp cimport bool as cbool


cdef extern from "thorvg_capi.h" nogil:

    # Opaque handles - typedef'd as pointers to incomplete structs in the C
    # header. Treat as ``void *`` on the Cython side.
    ctypedef void *Tvg_Canvas
    ctypedef void *Tvg_Paint
    ctypedef void *Tvg_Animation
    ctypedef void *Tvg_Accessor

    # Enums
    ctypedef enum Tvg_Result:
        TVG_RESULT_SUCCESS
        TVG_RESULT_INVALID_ARGUMENT
        TVG_RESULT_INSUFFICIENT_CONDITION
        TVG_RESULT_FAILED_ALLOCATION
        TVG_RESULT_MEMORY_CORRUPTION
        TVG_RESULT_NOT_SUPPORTED
        TVG_RESULT_UNKNOWN

    ctypedef enum Tvg_Colorspace:
        TVG_COLORSPACE_ABGR8888
        TVG_COLORSPACE_ARGB8888
        TVG_COLORSPACE_ABGR8888S
        TVG_COLORSPACE_ARGB8888S
        TVG_COLORSPACE_UNKNOWN

    ctypedef enum Tvg_Engine_Option:
        TVG_ENGINE_OPTION_NONE
        TVG_ENGINE_OPTION_DEFAULT
        TVG_ENGINE_OPTION_SMART_RENDER

    # Accessor traversal callback signature.
    ctypedef cbool (*Tvg_Accessor_Func)(Tvg_Paint paint, void *data)

    # --- Engine (refcounted singleton at the C layer) ---
    Tvg_Result tvg_engine_init(unsigned threads)
    Tvg_Result tvg_engine_term()
    Tvg_Result tvg_engine_version(uint32_t *major, uint32_t *minor,
                                  uint32_t *micro, const char **version)

    # --- SwCanvas ---
    Tvg_Canvas tvg_swcanvas_create(Tvg_Engine_Option op)
    Tvg_Result tvg_swcanvas_set_target(
        Tvg_Canvas canvas, uint32_t *buffer, uint32_t stride,
        uint32_t w, uint32_t h, Tvg_Colorspace cs)

    # --- Canvas (common) ---
    Tvg_Result tvg_canvas_destroy(Tvg_Canvas canvas)
    Tvg_Result tvg_canvas_add(Tvg_Canvas canvas, Tvg_Paint paint)
    Tvg_Result tvg_canvas_remove(Tvg_Canvas canvas, Tvg_Paint paint)
    Tvg_Result tvg_canvas_update(Tvg_Canvas canvas)
    Tvg_Result tvg_canvas_draw(Tvg_Canvas canvas, cbool clear)
    Tvg_Result tvg_canvas_sync(Tvg_Canvas canvas)

    # --- Paint (base) ---
    uint16_t tvg_paint_ref(Tvg_Paint paint)
    uint16_t tvg_paint_unref(Tvg_Paint paint, cbool free)
    Tvg_Result tvg_paint_set_opacity(Tvg_Paint paint, uint8_t opacity)
    uint32_t tvg_paint_get_id(const Tvg_Paint paint)

    # --- Picture ---
    Tvg_Paint tvg_picture_new()
    Tvg_Result tvg_picture_load(Tvg_Paint picture, const char *path)
    Tvg_Result tvg_picture_load_data(
        Tvg_Paint picture, const char *data, uint32_t size,
        const char *mimetype, const char *rpath, cbool copy)
    Tvg_Result tvg_picture_set_size(Tvg_Paint picture, float w, float h)
    Tvg_Result tvg_picture_get_size(const Tvg_Paint picture,
                                    float *w, float *h)
    const Tvg_Paint tvg_picture_get_paint(Tvg_Paint picture, uint32_t id)
    Tvg_Result tvg_picture_set_accessible(Tvg_Paint picture, cbool accessible)

    # --- Accessor ---
    Tvg_Accessor tvg_accessor_new()
    Tvg_Result tvg_accessor_del(Tvg_Accessor accessor)
    Tvg_Result tvg_accessor_set(
        Tvg_Accessor accessor, Tvg_Paint paint,
        Tvg_Accessor_Func func, void *data)
    uint32_t tvg_accessor_generate_id(const char *name)
    const char *tvg_accessor_get_name(Tvg_Accessor accessor, uint32_t id)

    # --- Animation (base) ---
    Tvg_Result tvg_animation_set_frame(Tvg_Animation animation, float no)
    Tvg_Paint tvg_animation_get_picture(Tvg_Animation animation)
    Tvg_Result tvg_animation_get_total_frame(Tvg_Animation animation,
                                             float *cnt)
    Tvg_Result tvg_animation_get_duration(Tvg_Animation animation,
                                          float *duration)
    Tvg_Result tvg_animation_set_segment(Tvg_Animation animation,
                                         float begin, float end)
    Tvg_Result tvg_animation_del(Tvg_Animation animation)

    # --- LottieAnimation ---
    Tvg_Animation tvg_lottie_animation_new()
    uint32_t tvg_lottie_animation_gen_slot(Tvg_Animation animation,
                                           const char *slot)
    Tvg_Result tvg_lottie_animation_apply_slot(Tvg_Animation animation,
                                               uint32_t id)
    Tvg_Result tvg_lottie_animation_del_slot(Tvg_Animation animation,
                                             uint32_t id)
    Tvg_Result tvg_lottie_animation_set_marker(Tvg_Animation animation,
                                               const char *marker)
    Tvg_Result tvg_lottie_animation_get_markers_cnt(Tvg_Animation animation,
                                                    uint32_t *cnt)
    Tvg_Result tvg_lottie_animation_get_marker(Tvg_Animation animation,
                                               uint32_t idx,
                                               const char **name)
    Tvg_Result tvg_lottie_animation_set_quality(Tvg_Animation animation,
                                                uint8_t value)

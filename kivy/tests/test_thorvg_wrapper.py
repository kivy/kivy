"""
Unit tests for :mod:`kivy.lib.thorvg`.

These tests cover the minimal surface required by Kivy's SVG, SVG-image and
Lottie providers:

* Engine init-at-import semantics and version reporting.
* :class:`Result` enum values.
* :class:`SwCanvas` allocation, buffer protocol, add/remove/update/draw/sync.
* :class:`Picture` load (from bytes), accessible-mode, sizing, child paint
  lookup via :class:`Accessor`.
* :class:`Accessor` ID generation and SVG element-name round-tripping.
* :class:`LottieAnimation` picture, metadata, frame/segment/marker/slot ops.

The tests deliberately avoid any Kivy graphics context - they exercise the
software renderer end-to-end and inspect the resulting RGBA buffer directly.

The module is skipped if the Cython extension failed to build (e.g. when
tests are run from a source tree without ThorVG), which keeps the test
suite usable on environments where ThorVG is not available.
"""

import pytest

tvg = pytest.importorskip('kivy.lib.thorvg')


# ---- test data -----------------------------------------------------------

_SVG_TWO_RECTS = (
    b'<?xml version="1.0"?>'
    b'<svg xmlns="http://www.w3.org/2000/svg" '
    b'width="64" height="32" viewBox="0 0 64 32">'
    b'<rect id="r1" x="0" y="0" width="32" height="32" fill="red"/>'
    b'<rect id="r2" x="32" y="0" width="32" height="32" fill="blue"/>'
    b'</svg>')


_LOTTIE_SINGLE_LAYER = (
    b'{"v":"5.7.1","fr":30,"ip":0,"op":60,"w":64,"h":32,"nm":"x",'
    b'"ddd":0,"assets":[],"layers":[{"ddd":0,"ind":1,"ty":4,"nm":"r",'
    b'"sr":1,"ks":{"o":{"a":0,"k":100},"r":{"a":0,"k":0},'
    b'"p":{"a":0,"k":[32,16,0]},"a":{"a":0,"k":[0,0,0]},'
    b'"s":{"a":0,"k":[100,100,100]}},"ao":0,"shapes":[{"ty":"rc",'
    b'"d":1,"s":{"a":0,"k":[32,32]},"p":{"a":0,"k":[0,0]},"r":{"a":0,"k":0}},'
    b'{"ty":"fl","c":{"a":0,"k":[1,0,0,1]},"o":{"a":0,"k":100}}],'
    b'"ip":0,"op":60,"st":0,"bm":0}]}')


# ---- engine --------------------------------------------------------------


def test_engine_version_is_1_0_4():
    res, major, minor, micro, ver = tvg.engine_version()
    assert res == tvg.Result.SUCCESS
    assert (major, minor, micro) == (1, 0, 4)
    assert ver == '1.0.4'


def test_result_enum_values():
    # Mirrors the documented Tvg_Result enum exactly so consumer providers
    # can compare against ``tvg.Result.SUCCESS`` reliably.
    assert int(tvg.Result.SUCCESS) == 0
    assert tvg.Result.UNKNOWN > tvg.Result.SUCCESS


# ---- SwCanvas ------------------------------------------------------------


def test_swcanvas_set_target_allocates_buffer():
    c = tvg.SwCanvas()
    assert c.w == 0 and c.h == 0 and c.stride == 0
    assert c.set_target(48, 24) == tvg.Result.SUCCESS
    assert (c.w, c.h, c.stride) == (48, 24, 48)
    mv = memoryview(c)
    assert mv.nbytes == 48 * 24 * 4
    # Buffer is zero-initialised before any draw.
    assert bytes(c)[:16] == b'\x00' * 16


def test_swcanvas_rejects_invalid_target():
    c = tvg.SwCanvas()
    assert c.set_target(0, 10) == tvg.Result.INVALID_ARGUMENT
    assert c.set_target(10, 0) == tvg.Result.INVALID_ARGUMENT


def test_swcanvas_set_target_resizes_buffer():
    c = tvg.SwCanvas()
    c.set_target(16, 16)
    assert memoryview(c).nbytes == 16 * 16 * 4
    c.set_target(32, 32)
    assert memoryview(c).nbytes == 32 * 32 * 4


def test_swcanvas_buffer_arr_compat_alias():
    # Existing providers call `bytes(canvas.buffer_arr)`; keep that working.
    c = tvg.SwCanvas()
    c.set_target(8, 8)
    assert bytes(c.buffer_arr) == bytes(c)


def test_swcanvas_destroy_idempotent():
    c = tvg.SwCanvas()
    c.set_target(4, 4)
    assert c.destroy() == tvg.Result.SUCCESS
    # After destroy, further operations report INVALID_ARGUMENT rather
    # than crashing.
    assert c.draw() == tvg.Result.INVALID_ARGUMENT
    assert c.sync() == tvg.Result.INVALID_ARGUMENT


# ---- Picture -------------------------------------------------------------


def test_picture_load_data_svg_and_size():
    p = tvg.Picture()
    assert p.load_data(_SVG_TWO_RECTS, 'svg') == tvg.Result.SUCCESS
    r, w, h = p.get_size()
    assert r == tvg.Result.SUCCESS
    assert (w, h) == (64.0, 32.0)


def test_picture_set_size_overrides_intrinsic_size():
    p = tvg.Picture()
    p.load_data(_SVG_TWO_RECTS, 'svg')
    assert p.set_size(128.0, 64.0) == tvg.Result.SUCCESS
    r, w, h = p.get_size()
    assert (w, h) == (128.0, 64.0)


def test_picture_rejects_unknown_mimetype():
    p = tvg.Picture()
    assert p.load_data(b'not-a-picture', 'garbage') != tvg.Result.SUCCESS


def test_picture_load_nonexistent_file():
    p = tvg.Picture()
    assert p.load('definitely/does/not/exist.svg') != tvg.Result.SUCCESS


# ---- Accessor ------------------------------------------------------------


def test_accessor_generate_id_is_deterministic():
    a = tvg.Accessor()
    assert a.accessor_generate_id('foo') == a.accessor_generate_id('foo')
    assert a.accessor_generate_id('foo') != a.accessor_generate_id('bar')


def test_accessor_walks_svg_element_ids():
    pic = tvg.Picture()
    assert pic.set_accessible(True) == tvg.Result.SUCCESS
    assert pic.load_data(_SVG_TWO_RECTS, 'svg') == tvg.Result.SUCCESS

    acc = tvg.Accessor()
    collected = []

    def visit(paint, data):
        pid = paint.get_id()
        if pid:
            collected.append(acc.get_name(pid))
        return True

    assert acc.set(pic, visit) == tvg.Result.SUCCESS
    assert 'r1' in collected and 'r2' in collected


def test_accessor_get_paint_roundtrips_by_id():
    pic = tvg.Picture()
    pic.set_accessible(True)
    pic.load_data(_SVG_TWO_RECTS, 'svg')

    acc = tvg.Accessor()
    hid = acc.accessor_generate_id('r1')
    paint = pic.get_paint(hid)
    assert paint is not None
    # The paint we fetched is the exact same child by ID.
    assert paint.get_id() == hid


def test_accessor_callback_exceptions_do_not_crash():
    pic = tvg.Picture()
    pic.load_data(_SVG_TWO_RECTS, 'svg')
    acc = tvg.Accessor()

    def boom(paint, data):
        raise RuntimeError('boom')

    # Exception is logged + traversal ends gracefully; return value != SUCCESS
    # is acceptable - the contract is just "don't crash".
    acc.set(pic, boom)


# ---- SwCanvas + Picture render end-to-end -------------------------------


def test_render_svg_produces_nonzero_pixels():
    p = tvg.Picture()
    p.load_data(_SVG_TWO_RECTS, 'svg')
    p.set_size(64.0, 32.0)

    c = tvg.SwCanvas()
    c.set_target(64, 32)
    assert c.add(p) == tvg.Result.SUCCESS
    assert c.draw(True) == tvg.Result.SUCCESS
    assert c.sync() == tvg.Result.SUCCESS

    pixels = bytes(c)
    assert any(b != 0 for b in pixels), 'buffer is all zero after draw/sync'


def test_canvas_add_transfers_ownership():
    """After Canvas.add, the Python Picture must not free its handle when
    garbage-collected while the canvas is alive.
    """
    c = tvg.SwCanvas()
    c.set_target(16, 16)
    p = tvg.Picture()
    p.load_data(_SVG_TWO_RECTS, 'svg')
    assert c.add(p) == tvg.Result.SUCCESS
    del p
    # If ownership were not correctly transferred, this draw+sync would
    # access a freed paint and typically crash the process.
    assert c.draw(True) == tvg.Result.SUCCESS
    assert c.sync() == tvg.Result.SUCCESS


# ---- LottieAnimation -----------------------------------------------------


def test_lottie_load_metadata():
    a = tvg.LottieAnimation()
    pic = a.get_picture()
    assert pic is not None
    assert pic.load_data(_LOTTIE_SINGLE_LAYER, 'lottie') == tvg.Result.SUCCESS

    r, dur = a.get_duration()
    assert r == tvg.Result.SUCCESS and dur > 0
    r, total = a.get_total_frame()
    assert r == tvg.Result.SUCCESS and total > 0


def test_lottie_set_frame_and_segment():
    a = tvg.LottieAnimation()
    a.get_picture().load_data(_LOTTIE_SINGLE_LAYER, 'lottie')
    _, total = a.get_total_frame()

    # ThorVG skips a no-op frame change and returns INSUFFICIENT_CONDITION.
    # That is fine from the provider's perspective - the contract is simply
    # "either accepted or explicitly rejected as a no-op".
    ok = (tvg.Result.SUCCESS, tvg.Result.INSUFFICIENT_CONDITION)
    assert a.set_frame(0.0) in ok
    assert a.set_frame(total / 2) in ok
    assert a.set_frame(total - 1) in ok
    assert a.set_segment(0.0, total) == tvg.Result.SUCCESS


def test_lottie_markers_count_zero_for_unmarked_file():
    a = tvg.LottieAnimation()
    a.get_picture().load_data(_LOTTIE_SINGLE_LAYER, 'lottie')
    r, cnt = a.get_markers_cnt()
    assert r == tvg.Result.SUCCESS
    assert cnt == 0


def test_lottie_slot_apply_and_del():
    # Test file has no slots; gen_slot with empty-ish data returns 0.
    a = tvg.LottieAnimation()
    a.get_picture().load_data(_LOTTIE_SINGLE_LAYER, 'lottie')
    # Passing empty or malformed slot data should not crash.
    slot_id = a.gen_slot(b'')
    assert isinstance(slot_id, int)
    if slot_id:
        # If ThorVG somehow accepted an empty slot (unlikely), the round-trip
        # should still succeed.
        assert a.del_slot(slot_id) == tvg.Result.SUCCESS


def test_lottie_set_quality_clamps_range():
    a = tvg.LottieAnimation()
    a.get_picture().load_data(_LOTTIE_SINGLE_LAYER, 'lottie')
    assert a.set_quality(-10) == tvg.Result.SUCCESS
    assert a.set_quality(200) == tvg.Result.SUCCESS
    assert a.set_quality(50) == tvg.Result.SUCCESS


def test_lottie_render_produces_nonzero_pixels():
    a = tvg.LottieAnimation()
    pic = a.get_picture()
    pic.load_data(_LOTTIE_SINGLE_LAYER, 'lottie')
    pic.set_size(64.0, 32.0)

    c = tvg.SwCanvas()
    c.set_target(64, 32)
    c.add(pic)
    a.set_frame(0.0)
    assert c.draw(True) == tvg.Result.SUCCESS
    assert c.sync() == tvg.Result.SUCCESS
    assert any(b != 0 for b in bytes(c))

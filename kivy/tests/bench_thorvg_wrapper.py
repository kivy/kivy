"""
Micro-benchmarks for :mod:`kivy.lib.thorvg`.

Measures the hot paths that the SVG / SVG-image / Lottie providers exercise
during steady-state playback:

* Picture load_data for a small SVG.
* SwCanvas allocation + set_target.
* Steady-state SVG render (update → draw → sync).
* Steady-state Lottie frame advance + render.
* Texture upload hand-off: the zero-copy buffer-protocol path that
  :meth:`kivy.graphics.texture.Texture.blit_buffer` actually consumes,
  contrasted against a ``bytes(canvas)`` baseline that forces a full copy.
  The gap between the two is the whole reason ``SwCanvas`` implements
  ``__getbuffer__``; these two benchmarks are what we regression-guard
  against accidentally falling back to copy-on-every-frame.

These are provider-independent: they do not touch the Kivy graphics context
and can run headlessly in CI. Results are recorded via pytest-benchmark and
appear in CI JSON artefacts for regression tracking.

Run locally with:

    pytest kivy/tests/bench_thorvg_wrapper.py --benchmark-only

Skipped automatically if either :mod:`kivy.lib.thorvg` or
``pytest-benchmark`` is unavailable.
"""

import pytest

tvg = pytest.importorskip('kivy.lib.thorvg')
pytest.importorskip('pytest_benchmark')


_SVG = (
    b'<?xml version="1.0"?>'
    b'<svg xmlns="http://www.w3.org/2000/svg" '
    b'width="256" height="256" viewBox="0 0 256 256">'
    b'<circle id="c" cx="128" cy="128" r="100" fill="orange"/>'
    b'<rect id="r" x="32" y="32" width="64" height="64" fill="red"/>'
    b'<path id="p" d="M10 10 L200 10 L200 200 Z" '
    b'fill="green" stroke="black" stroke-width="4"/>'
    b'</svg>')

_LOTTIE = (
    b'{"v":"5.7.1","fr":30,"ip":0,"op":60,"w":128,"h":128,"nm":"x",'
    b'"ddd":0,"assets":[],"layers":[{"ddd":0,"ind":1,"ty":4,"nm":"r",'
    b'"sr":1,"ks":{"o":{"a":0,"k":100},"r":{"a":1,"k":['
    b'{"t":0,"s":[0]},{"t":60,"s":[360]}]},'
    b'"p":{"a":0,"k":[64,64,0]},"a":{"a":0,"k":[0,0,0]},'
    b'"s":{"a":0,"k":[100,100,100]}},"ao":0,"shapes":[{"ty":"rc",'
    b'"d":1,"s":{"a":0,"k":[64,64]},"p":{"a":0,"k":[0,0]},'
    b'"r":{"a":0,"k":0}},'
    b'{"ty":"fl","c":{"a":0,"k":[0.2,0.4,0.9,1]},"o":{"a":0,"k":100}}],'
    b'"ip":0,"op":60,"st":0,"bm":0}]}')


def test_bench_picture_load_svg(benchmark):
    def load():
        p = tvg.Picture()
        p.load_data(_SVG, 'svg', None, True)
        return p
    benchmark(load)


def test_bench_swcanvas_set_target_256(benchmark):
    def allocate():
        c = tvg.SwCanvas()
        c.set_target(256, 256)
        return c
    benchmark(allocate)


def test_bench_svg_render_steady_state(benchmark):
    """Simulates every-frame cost once the scene has been added."""
    p = tvg.Picture()
    p.load_data(_SVG, 'svg', None, True)
    p.set_size(256.0, 256.0)

    c = tvg.SwCanvas()
    c.set_target(256, 256)
    c.add(p)

    def draw():
        c.update()
        c.draw(True)
        c.sync()

    benchmark(draw)


def _rendered_canvas(width=256, height=256):
    p = tvg.Picture()
    p.load_data(_SVG, 'svg', None, True)
    p.set_size(float(width), float(height))
    c = tvg.SwCanvas()
    c.set_target(width, height)
    c.add(p)
    c.draw(True)
    c.sync()
    return c


def test_bench_svg_buffer_memoryview(benchmark):
    """Zero-copy hand-off to the GPU upload path.

    This is the code path providers should use when feeding
    :meth:`kivy.graphics.texture.Texture.blit_buffer`, which explicitly
    accepts any object exporting the Python buffer protocol. The
    benchmark wraps the canvas in a :class:`memoryview`, which is what
    ``blit_buffer`` does internally; no bytes are copied.

    Expected to be roughly one to two orders of magnitude faster than
    :func:`test_bench_svg_buffer_bytes_copy` on a 256x256 RGBA target.
    """
    c = _rendered_canvas()
    benchmark(lambda: memoryview(c))


def test_bench_svg_buffer_bytes_copy(benchmark):
    """Worst-case texture upload path: explicit ``bytes(...)`` copy.

    Kept as a regression baseline: if a future refactor accidentally
    makes providers go through ``bytes(canvas.buffer_arr)`` on every
    frame, the resulting ~256 KiB/frame copy shows up as a large gap
    between this benchmark and
    :func:`test_bench_svg_buffer_memoryview`. This benchmark is
    deliberately **not** the pattern we recommend for providers.
    """
    c = _rendered_canvas()
    benchmark(lambda: bytes(c.buffer_arr))


def test_bench_lottie_frame_advance(benchmark):
    a = tvg.LottieAnimation()
    pic = a.get_picture()
    pic.load_data(_LOTTIE, 'lottie', None, True)
    pic.set_size(128.0, 128.0)

    c = tvg.SwCanvas()
    c.set_target(128, 128)
    c.add(pic)

    _, total = a.get_total_frame()
    # Cycle through a handful of frames per benchmark iteration so timings
    # average over frame-specific fast paths (keyframe vs interpolated).
    frames = [total * (i / 8.0) for i in range(8)]

    def tick():
        for f in frames:
            a.set_frame(f)
            c.update()
            c.draw(True)
            c.sync()

    benchmark(tick)

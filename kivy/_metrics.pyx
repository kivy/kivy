"""Low level Metrics
====================

Module for low level metrics operations.

"""
__all__ = ('dpi2px', 'NUMERIC_FORMATS', 'dispatch_pixel_scale')


cdef float g_dpi = -1
cdef float g_density = -1
cdef float g_fontscale = -1
cdef EventObservers pixel_scale_observers = EventObservers.__new__(
    EventObservers)
"""These observers are dispatched when the dpi/density/font scale changes.
All NumericProperties bind to it, and dispatch their prop in response (if it
causes changes to them).
"""
NUMERIC_FORMATS = ('in', 'px', 'dp', 'sp', 'pt', 'cm', 'mm')
"""The tuple of supported suffixes in Kivy properties that support e.g.
``"10dp"`` type syntax.
"""


def dispatch_pixel_scale(*args):
    """Dispatches all properties that and watch pixel_scale_observers.

    This should be called by Metrics when it changes any of the scaling
    properties.
    """
    from kivy.metrics import Metrics
    global g_dpi, g_density, g_fontscale

    g_dpi = Metrics.dpi
    g_density = Metrics.density
    g_fontscale = Metrics.fontscale
    pixel_scale_observers.dispatch(None, None, None, None, 0)


cpdef float dpi2px(value, str ext) except *:
    """Converts the value according to the ext."""
    # 1in = 2.54cm = 25.4mm = 72pt = 12pc
    if g_dpi == -1:
        dispatch_pixel_scale()


    cdef float rv = <float>float(value)
    if ext == 'in':
        return rv * g_dpi
    elif ext == 'px':
        return rv
    elif ext == 'dp':
        return rv * g_density
    elif ext == 'sp':
        return rv * g_density * g_fontscale
    elif ext == 'pt':
        return rv * g_dpi / <float>72.
    elif ext == 'cm':
        return rv * g_dpi / <float>2.54
    elif ext == 'mm':
        return rv * g_dpi / <float>25.4

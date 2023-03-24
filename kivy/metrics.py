'''
Metrics
=======

.. versionadded:: 1.5.0

A screen is defined by its physical size, density and resolution. These
factors are essential for creating UI's with correct size everywhere.

In Kivy, all the graphics pipelines work with pixels. But using pixels as a
measurement unit is problematic because sizes change according to the
screen.

Dimensions
----------

If you want to design your UI for different screen sizes, you will want better
measurement units to work with. Kivy provides some more scalable alternatives.

:Units:
    `pt`
        Points - 1/72 of an inch based on the physical size of the screen.
        Prefer to use sp instead of pt.
    `mm`
        Millimeters - Based on the physical size of the screen.
    `cm`
        Centimeters - Based on the physical size of the screen.
    `in`
        Inches - Based on the physical size of the screen.
    `dp`
        Density-independent Pixels - An abstract unit that is based on the
        physical density of the screen. With a :attr:`~MetricsBase.density` of
        1, 1dp is equal to 1px. When running on a higher density screen, the
        number of pixels used to draw 1dp is scaled up a factor appropriate to
        the screen's dpi, and the inverse for a lower dpi.
        The ratio of dp-to-pixels will change with the screen density, but not
        necessarily in direct proportion. Using the dp unit is a simple
        solution to making the view dimensions in your layout resize
        properly for different screen densities. In others words, it
        provides consistency for the real-world size of your UI across
        different devices.
    `sp`
        Scale-independent Pixels - This is like the dp unit, but it is also
        scaled by the user's font size preference. We recommend you use this
        unit when specifying font sizes, so the font size will be adjusted to
        both the screen density and the user's preference.

Examples
--------

Here is an example of creating a label with a sp font_size and setting the
height manually with a 10dp margin::

    #:kivy 1.5.0
    <MyWidget>:
        Label:
            text: 'Hello world'
            font_size: '15sp'
            size_hint_y: None
            height: self.texture_size[1] + dp(10)

Manual control of metrics
-------------------------

The metrics cannot be changed at runtime. Once a value has been converted to
pixels, you can't retrieve the original value anymore. This stems from the fact
that the DPI and density of a device cannot be changed at runtime.

We provide some environment variables to control metrics:

- `KIVY_METRICS_DENSITY`: if set, this value will be used for
  :attr:`~MetricsBase.density` instead of the systems one. On android,
  the value varies between 0.75, 1, 1.5 and 2.

- `KIVY_METRICS_FONTSCALE`: if set, this value will be used for
  :attr:`~MetricsBase.fontscale` instead of the systems one. On android, the
  value varies between 0.8 and 1.2.

- `KIVY_DPI`: if set, this value will be used for :attr:`~MetricsBase.dpi`.
  Please
  note that setting the DPI will not impact the dp/sp notation because these
  are based on the screen density.

For example, if you want to simulate a high-density screen (like the HTC One
X)::

    KIVY_DPI=320 KIVY_METRICS_DENSITY=2 python main.py --size 1280x720

Or a medium-density (like Motorola Droid 2)::

    KIVY_DPI=240 KIVY_METRICS_DENSITY=1.5 python main.py --size 854x480

You can also simulate an alternative user preference for fontscale as follows::

    KIVY_METRICS_FONTSCALE=1.2 python main.py

'''


from os import environ
from kivy.utils import platform
from kivy.properties import AliasProperty
from kivy.event import EventDispatcher
from kivy.setupconfig import USE_SDL2
from kivy.context import register_context
from kivy._metrics import dpi2px, NUMERIC_FORMATS, dispatch_pixel_scale, \
    sync_pixel_scale


__all__ = (
    'Metrics', 'MetricsBase', 'pt', 'inch', 'cm', 'mm', 'dp', 'sp', 'dpi2px',
    'NUMERIC_FORMATS')


_default_dpi = None
_default_density = None
_default_fontscale = None
if environ.get('KIVY_DOC_INCLUDE', None) == '1':
    _default_dpi = 132.
    _default_density = 1
else:
    _custom_dpi = environ.get('KIVY_DPI')
    if _custom_dpi:
        _default_dpi = float(_custom_dpi)

    _custom_density = environ.get('KIVY_METRICS_DENSITY')
    if _custom_density:
        _default_density = float(_custom_density)

    _custom_fontscale = environ.get('KIVY_METRICS_FONTSCALE')
    if _custom_fontscale:
        _default_fontscale = float(_custom_fontscale)


def pt(value) -> float:
    '''Convert from points to pixels
    '''
    return dpi2px(value, 'pt')


def inch(value) -> float:
    '''Convert from inches to pixels
    '''
    return dpi2px(value, 'in')


def cm(value) -> float:
    '''Convert from centimeters to pixels
    '''
    return dpi2px(value, 'cm')


def mm(value) -> float:
    '''Convert from millimeters to pixels
    '''
    return dpi2px(value, 'mm')


def dp(value) -> float:
    '''Convert from density-independent pixels to pixels
    '''
    return dpi2px(value, 'dp')


def sp(value) -> float:
    '''Convert from scale-independent pixels to pixels
    '''
    return dpi2px(value, 'sp')


class MetricsBase(EventDispatcher):
    '''Class that contains the default attributes for Metrics. Don't use this
    class directly, but use the `Metrics` instance.
    '''

    _dpi = _default_dpi

    _density = _default_density

    _fontscale = _default_fontscale

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fbind('dpi', dispatch_pixel_scale)
        self.fbind('density', dispatch_pixel_scale)
        self.fbind('fontscale', dispatch_pixel_scale)

    def get_dpi(self, force_recompute=False):
        if not force_recompute and self._dpi is not None:
            return self._dpi

        if platform == 'android':
            if USE_SDL2:
                import jnius
                Hardware = jnius.autoclass('org.renpy.android.Hardware')
                value = Hardware.getDPI()
            else:
                import android
                value = android.get_dpi()
        elif platform == 'ios':
            import ios
            value = ios.get_dpi()
        else:
            # for all other platforms..
            from kivy.base import EventLoop
            EventLoop.ensure_window()
            value = EventLoop.window.dpi

        # because dp prop binds to dpi etc. its getter will be executed
        # before dispatch_pixel_scale bound to dpi was called, so we need to
        # call this to make sure it's updated
        sync_pixel_scale(dpi=value)
        return value

    def set_dpi(self, value):
        self._dpi = value
        sync_pixel_scale(dpi=value)
        return True

    dpi: float = AliasProperty(get_dpi, set_dpi, cache=True)
    '''The DPI of the screen.

    Depending on the platform, the DPI can be taken from the Window provider
    (Desktop mainly) or from a platform-specific module (like android/ios).

    :attr:`dpi` is a :class:`~kivy.properties.AliasProperty` and can be
    set to change the value. But, the :attr:`density` is reloaded and reset if
    we got it from the Window and the Window ``dpi`` changed.
    '''

    def get_dpi_rounded(self):
        dpi = self.dpi
        if dpi < 140:
            return 120
        elif dpi < 200:
            return 160
        elif dpi < 280:
            return 240
        return 320

    dpi_rounded: int = AliasProperty(
        get_dpi_rounded, None, bind=('dpi', ), cache=True)
    '''Return the :attr:`dpi` of the screen, rounded to the nearest of 120,
    160, 240 or 320.

    :attr:`dpi_rounded` is a :class:`~kivy.properties.AliasProperty` and
    updates when :attr:`dpi` changes.
    '''

    def get_density(self, force_recompute=False):
        if not force_recompute and self._density is not None:
            return self._density

        value = 1.0
        if platform == 'android':
            import jnius
            Hardware = jnius.autoclass('org.renpy.android.Hardware')
            value = Hardware.metrics.scaledDensity
        elif platform == 'ios':
            import ios
            value = ios.get_scale()
        elif platform in ('macosx', 'win'):
            value = self.dpi / 96.

        sync_pixel_scale(density=value)
        return value

    def set_density(self, value):
        self._density = value
        sync_pixel_scale(density=value)
        return True

    density: float = AliasProperty(
        get_density, set_density, bind=('dpi', ), cache=True)
    '''The density of the screen.

    This value is 1 by default on desktops but varies on android depending on
    the screen.

    :attr:`density` is a :class:`~kivy.properties.AliasProperty` and can be
    set to change the value. But, the :attr:`density` is reloaded and reset if
    we got it from the Window and the Window ``density`` changed.
    '''

    def get_fontscale(self, force_recompute=False):
        if not force_recompute and self._fontscale is not None:
            return self._fontscale

        value = 1.0
        if platform == 'android':
            from jnius import autoclass
            if USE_SDL2:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
            else:
                PythonActivity = autoclass('org.renpy.android.PythonActivity')
            config = PythonActivity.mActivity.getResources().getConfiguration()
            value = config.fontScale

        sync_pixel_scale(fontscale=value)
        return value

    def set_fontscale(self, value):
        self._fontscale = value
        sync_pixel_scale(fontscale=value)
        return True

    fontscale: float = AliasProperty(get_fontscale, set_fontscale, cache=True)
    '''The fontscale user preference.

    This value is 1 by default but can vary between 0.8 and 1.2.

    :attr:`fontscale` is a :class:`~kivy.properties.AliasProperty` and can be
    set to change the value.
    '''

    def get_in(self):
        # we bind to all dpi, density, fontscale, even though not all may be
        # used for a specific suffix, because we don't want to rely on the
        # internal details of dpi2px. But it will be one of the three. But it's
        # an issue, since it won't trigger the prop if the value doesn't change
        return dpi2px(1, 'in')

    inch: float = AliasProperty(
        get_in, None, bind=('dpi', 'density', 'fontscale'), cache=True)
    """The scaling factor that converts from inches to pixels.

    :attr:`inch` is a :class:`~kivy.properties.AliasProperty` containing the
    factor. E.g in KV: ``width: self.texture_size[0] + 10 * Metrics.inch`` will
    update width when :attr:`inch` changes from a screen configuration change.
    """

    def get_dp(self):
        return dpi2px(1, 'dp')

    dp: float = AliasProperty(
        get_dp, None, bind=('dpi', 'density', 'fontscale'), cache=True)
    """The scaling factor that converts from density-independent pixels to
    pixels.

    :attr:`dp` is a :class:`~kivy.properties.AliasProperty` containing the
    factor. E.g in KV: ``width: self.texture_size[0] + 10 * Metrics.dp`` will
    update width when :attr:`dp` changes from a screen configuration change.
    """

    def get_sp(self):
        return dpi2px(1, 'sp')

    sp: float = AliasProperty(
        get_sp, None, bind=('dpi', 'density', 'fontscale'), cache=True)
    """The scaling factor that converts from scale-independent pixels to
    pixels.

    :attr:`sp` is a :class:`~kivy.properties.AliasProperty` containing the
    factor. E.g in KV: ``width: self.texture_size[0] + 10 * Metrics.sp`` will
    update width when :attr:`sp` changes from a screen configuration change.
    """

    def get_pt(self):
        return dpi2px(1, 'pt')

    pt: float = AliasProperty(
        get_pt, None, bind=('dpi', 'density', 'fontscale'), cache=True)
    """The scaling factor that converts from points to pixels.

    :attr:`pt` is a :class:`~kivy.properties.AliasProperty` containing the
    factor. E.g in KV: ``width: self.texture_size[0] + 10 * Metrics.pt`` will
    update width when :attr:`pt` changes from a screen configuration change.
    """

    def get_cm(self):
        return dpi2px(1, 'cm')

    cm: float = AliasProperty(
        get_cm, None, bind=('dpi', 'density', 'fontscale'), cache=True)
    """The scaling factor that converts from centimeters to pixels.

    :attr:`cm` is a :class:`~kivy.properties.AliasProperty` containing the
    factor. E.g in KV: ``width: self.texture_size[0] + 10 * Metrics.cm`` will
    update width when :attr:`cm` changes from a screen configuration change.
    """

    def get_mm(self):
        return dpi2px(1, 'mm')

    mm: float = AliasProperty(
        get_mm, None, bind=('dpi', 'density', 'fontscale'), cache=True)
    """The scaling factor that converts from millimeters to pixels.

    :attr:`mm` is a :class:`~kivy.properties.AliasProperty` containing the
    factor. E.g in KV: ``width: self.texture_size[0] + 10 * Metrics.mm`` will
    update width when :attr:`mm` changes from a screen configuration change.
    """

    def reset_metrics(self):
        """Resets the dpi/density/fontscale to the platform values, overwriting
        any manually set values.
        """
        self.dpi = self.get_dpi(force_recompute=True)
        self.density = self.get_density(force_recompute=True)
        self.fontscale = self.get_fontscale(force_recompute=True)

    def reset_dpi(self, *args):
        """Resets the dpi (and possibly density) to the platform values,
        overwriting any manually set values.
        """
        self.dpi = self.get_dpi(force_recompute=True)

    def _set_cached_scaling(self):
        dispatch_pixel_scale()


Metrics: MetricsBase = register_context('Metrics', MetricsBase)
"""The metrics object storing the window scaling factors.

.. versionadded:: 1.7.0

.. versionchanged:: 2.1.0

     :attr:`Metrics` is now a Context registered variable (like e.g.
     :attr:`~kivy.clock.Clock`).
"""

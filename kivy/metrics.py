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


__all__ = ('Metrics', 'MetricsBase', 'pt', 'inch', 'cm', 'mm', 'dp', 'sp')


from os import environ
from kivy.utils import reify, platform
from kivy.properties import dpi2px
from kivy.setupconfig import USE_SDL2


def pt(value):
    '''Convert from points to pixels
    '''
    return dpi2px(value, 'pt')


def inch(value):
    '''Convert from inches to pixels
    '''
    return dpi2px(value, 'in')


def cm(value):
    '''Convert from centimeters to pixels
    '''
    return dpi2px(value, 'cm')


def mm(value):
    '''Convert from millimeters to pixels
    '''
    return dpi2px(value, 'mm')


def dp(value):
    '''Convert from density-independent pixels to pixels
    '''
    return dpi2px(value, 'dp')


def sp(value):
    '''Convert from scale-independent pixels to pixels
    '''
    return dpi2px(value, 'sp')


class MetricsBase(object):
    '''Class that contains the default attributes for Metrics. Don't use this
    class directly, but use the `Metrics` instance.
    '''

    @reify
    def dpi(self):
        '''Return the DPI of the screen. Depending on the platform, the DPI can
        be taken from the Window provider (Desktop mainly) or from a
        platform-specific module (like android/ios).
        '''
        if environ.get('KIVY_DOC_INCLUDE', None):
            return 132.

        custom_dpi = environ.get('KIVY_DPI')
        if custom_dpi:
            return float(custom_dpi)

        if platform == 'android':
            if USE_SDL2:
                import jnius
                Hardware = jnius.autoclass('org.renpy.android.Hardware')
                return Hardware.getDPI()
            else:
                import android
                return android.get_dpi()
        elif platform == 'ios':
            import ios
            return ios.get_dpi()

        # for all other platforms..
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        return EventLoop.window.dpi

    @reify
    def dpi_rounded(self):
        '''Return the DPI of the screen, rounded to the nearest of 120, 160,
        240 or 320.
        '''
        dpi = self.dpi
        if dpi < 140:
            return 120
        elif dpi < 200:
            return 160
        elif dpi < 280:
            return 240
        return 320

    @reify
    def density(self):
        '''Return the density of the screen. This value is 1 by default
        on desktops but varies on android depending on the screen.
        '''
        if environ.get('KIVY_DOC_INCLUDE', None):
            return 1.

        custom_density = environ.get('KIVY_METRICS_DENSITY')
        if custom_density:
            return float(custom_density)

        if platform == 'android':
            import jnius
            Hardware = jnius.autoclass('org.renpy.android.Hardware')
            return Hardware.metrics.scaledDensity
        elif platform == 'ios':
            import ios
            return ios.get_scale()
        elif platform == 'macosx':
            from kivy.base import EventLoop
            EventLoop.ensure_window()
            return EventLoop.window.dpi / 96.

        return 1.0

    @reify
    def fontscale(self):
        '''Return the fontscale user preference. This value is 1 by default but
        can vary between 0.8 and 1.2.
        '''
        custom_fontscale = environ.get('KIVY_METRICS_FONTSCALE')
        if custom_fontscale:
            return float(custom_fontscale)

        if platform == 'android':
            from jnius import autoclass
            if USE_SDL2:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
            else:
                PythonActivity = autoclass('org.renpy.android.PythonActivity')
            config = PythonActivity.mActivity.getResources().getConfiguration()
            return config.fontScale

        return 1.0


#: Default instance of :class:`MetricsBase`, used everywhere in the code
#: .. versionadded:: 1.7.0
Metrics = MetricsBase()

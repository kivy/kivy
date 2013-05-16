'''
Metrics
=======

.. versionadded:: 1.5.0

A screen is defined by its actual physical size, density, resolution. These
factors are essential for creating UI with correct size everywhere.

In Kivy, all our graphics pipeline is working with pixels. But using pixels as a
measurement unit is wrong, because the size will changes according to the
screen.

Dimensions
----------

As you design your UI for different screen sizes, you'll need new measurement
unit to work with.

:Units:
    `pt`
        Points - 1/72 of an inch based on the physical size of the screen.
        Prefer to use sp instead of pt.
    `mm`
        Millimeters - Based on the physical size of the screen
    `cm`
        Centimeters - Based on the physical size of the screen
    `in`
        Inches - Based on the physical size of the screen
    `dp`
        Density-independent Pixels - An abstract unit that is based on the
        physical density of the screen. With a :data:`Metrics.density` of 1, 1dp
        is equal to 1px. When running on a higher density screen, the number of
        pixels used to draw 1dp is scaled up by the factor of appropriate
        screen's dpi, and the inverse for lower dpi.
        The ratio dp-to-pixes will change with the screen density, but not
        necessarily in direct proportions. Using dp unit is a simple solution to
        making the view dimensions in your layout resize properly for different
        screen densities. In others words, it provides consistency for the
        real-world size of your UI across different devices.
    `sp`
        Scale-independent Pixels - This is like the dp unit, but it is also
        scaled by the user's font size preference. It is recommended to use this
        unit when specifying font sizes, so they will be adjusted for both the
        screen density and the user's preference.

Examples
--------

An example of creating a label with a sp font_size, and set a manual height with
a 10dp margin::

    #:kivy 1.5.0
    <MyWidget>:
        Label:
            text: 'Hello world'
            font_size: '15sp'
            size_hint_y: None
            height: self.texture_size[1] + dp(10)

Manual control of metrics
-------------------------

The metrics cannot be changed in runtime. Once a value has been converted to
pixels, you don't have the original value anymore. It's not like you'll change
the DPI or density in runtime.

We provide new environment variables to control the metrics:

- `KIVY_METRICS_DENSITY`: if set, this value will be used for
  :data:`Metrics.density` instead of the system one. On android, the value
  varies between 0.75, 1, 1.5. 2.

- `KIVY_METRICS_FONTSCALE`: if set, this value will be used for
  :data:`Metrics.fontscale` instead of the system one. On android, the value
  varies between 0.8-1.2.

- `KIVY_DPI`: if set, this value will be used for :data:`Metrics.dpi`. Please
  note that settings the DPI will not impact dp/sp notation, because thoses are
  based on the density.

For example, if you want to simulate an high-density screen (like HTC One X)::

    KIVY_DPI=320 KIVY_METRICS_DENSITY=2 python main.py --size 1280x720

Or a medium-density (like Motorola Droid 2)::

    KIVY_DPI=240 KIVY_METRICS_DENSITY=1.5 python main.py --size 854x480

You can also simulate an alternative user preference for fontscale, like::

    KIVY_METRICS_FONTSCALE=1.2 python main.py

'''


__all__ = ('Metrics', 'MetricsBase', 'pt', 'inch', 'cm', 'mm', 'dp', 'sp',
'metrics')


from os import environ
from kivy.utils import reify, platform
from kivy.properties import dpi2px


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
    '''Class that contain the default attribute for metrics. Don't use the class
    directly, but use the `metrics` instance.
    '''

    @reify
    def dpi(self):
        '''Return the DPI of the screen. Depending of the platform, the DPI can
        be taken from the Window provider (Desktop mainly), or from
        platform-specific module (like android/ios).
        '''
        custom_dpi = environ.get('KIVY_DPI')
        if custom_dpi:
            return float(custom_dpi)

        if platform() == 'android':
            import android
            return android.get_dpi()
        elif platform() == 'ios':
            import ios
            return ios.get_dpi()

        # for all other platforms..
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        return EventLoop.window.dpi

    @reify
    def dpi_rounded(self):
        '''Return the dpi of the screen, rounded to the nearest of 120, 160,
        240, 320.
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
        on desktop, and varies on android depending the screen.
        '''
        custom_density = environ.get('KIVY_METRICS_DENSITY')
        if custom_density:
            return float(custom_density)

        if platform() == 'android':
            import jnius
            Hardware = jnius.autoclass('org.renpy.android.Hardware')
            return Hardware.metrics.scaledDensity
        elif platform() == 'ios':
            # 0.75 is for mapping the same density as android tablet
            import ios
            return ios.get_scale() * 0.75

        return 1.0

    @reify
    def fontscale(self):
        '''Return the fontscale user preference. This value is 1 by default, and
        can varies between 0.8-1.2.
        '''
        custom_fontscale = environ.get('KIVY_METRICS_FONTSCALE')
        if custom_fontscale:
            return float(custom_fontscale)

        if platform() == 'android':
            import jnius
            PythonActivity = jnius.autoclass('org.renpy.android.PythonActivity')
            config = PythonActivity.mActivity.getResources().getConfiguration()
            return config.fontScale

        return 1.0


#: default instance of :class:`MetricsBase`, used everywhere in the code
#: .. versionadded:: 1.7.0
Metrics = MetricsBase()

#: default instance of :class:`MetricsBase`, used everywhere in the code
#: (deprecated, use `Metrics` instead.)
metrics = Metrics

'''
Display Metrics
===============

This module give you access to multiple display values, and some conversion
functions.
'''

__all__ = ('metrics', 'Metrics', 'pt', 'inch', 'cm', 'mm', 'dp')

from os import environ
from kivy.utils import reify, platform
from kivy.properties import dpi2px

def pt(value):
    return dpi2px(value, 'pt')

def inch(value):
    return dpi2px(value, 'in')

def cm(value):
    return dpi2px(value, 'cm')

def mm(value):
    return dpi2px(value, 'mm')

def dp(value):
    return dpi2px(value, 'dp')

def sp(value):
    return dpi2px(value, 'sp')


class Metrics(object):

    @reify
    def dpi(self):
        '''Return the DPI of the screen. Depending of the platform, the DPI can
        be taken from the Window provider (Desktop mainly), or from
        platform-specific module (like android/ios).

        On desktop, you can overload the value returned by the Window object
        (96 by default), by setting the environ KIVY_DPI::

            KIVY_DPI=200 python main.py

        .. versionadded:: 1.4.0
        '''
        custom_dpi = environ.get('KIVY_DPI')
        if custom_dpi:
            return float(custom_dpi)

        if platform() == 'android':
            import android
            return android.get_dpi()

        # for all other platforms..
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        return EventLoop.window.dpi

    @reify
    def dpi_rounded(self):
        '''Return the dpi of the screen, rounded to the nearest of 120, 160,
        240, 320.

        .. versionadded:: 1.5.0
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
        custom_density = environ.get('KIVY_METRICS_DENSITY')
        if custom_density:
            return float(custom_density)

        if platform() == 'android':
            import jnius
            Hardware = jnius.autoclass('org.renpy.android.Hardware')
            return Hardware.metrics.scaledDensity

        return 1.0

    @reify
    def fontscale(self):
        custom_fontscale = environ.get('KIVY_METRICS_FONTSCALE')
        if custom_fontscale:
            return float(custom_fontscale)

        if platform() == 'android':
            import jnius
            PythonActivity = jnius.autoclass('org.renpy.android.PythonActivity')
            config = PythonActivity.mActivity.getResources().getConfiguration()
            return config.fontScale

        return 1.0


#: default instance of :class:`Metrics`, used everywhere in the code
metrics = Metrics()

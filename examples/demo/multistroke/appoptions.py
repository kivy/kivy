#!/usr/bin/env python
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.properties import StringProperty
from kivy.factory import Factory
from kivy.lang import Builder

# Local libraries
import touchanalyzer as TA

__all__ = ('AppOptions',)


class CustomSlider(Slider):

    watch_value = StringProperty(None)

    def __init__(self, **kwargs):
        super(CustomSlider, self).__init__(**kwargs)
        self.bind(value=self._set_value)

    def _set_value(self, instance, value):
        setattr(TA, self.watch_value, round(value, 1))

Factory.register('CustomSlider', cls=CustomSlider)
Builder.load_file('appoptions.kv')


class AppOptions(GridLayout):
    pass

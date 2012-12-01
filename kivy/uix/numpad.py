'''
NumPad
======

.. versionadded:: 1.5

.. warning::

    This widget is experimental. Its use and api can change any time, until
    thes warning is removed.

A widget to type in a number using positional notation

'''

from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty


class NumPad(Widget):
    display_text = StringProperty("0")
    display_value = NumericProperty(0)
    max_value = NumericProperty(10000)

    def __init__(self, popup, init_value=0, **kwargs):
        super(NumPad, self).__init__(**kwargs)
        if init_value <= 255 and init_value >= 0:
            self.display_text = str(int(init_value))
        self.popup = popup

    def button_callback(self, button_str):
        if button_str in [str(x) for x in range(10)]:
            if self.display_text == '0':
                self.display_text = button_str
            else:
                self.display_text += button_str

            if self.display_value > self.max_value:
                self.display_text = str(self.max_value)

        elif button_str == 'del':
            self.display_text = self.display_text[:-1]

        elif button_str == 'ret':
            self.popup.dismiss()

    def on_display_text(self, instance, value):
        if value == '':
            self.display_text = '0'
            return
        self.display_value = int(value)

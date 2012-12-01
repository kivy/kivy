'''
NumPad
======

.. versionadded:: 1.5

.. warning::

    This widget is experimental. Its use and api can change any time, until
    thes warning is removed.

A widget to type in a number using positional notation.

'''

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.properties import NumericProperty, ObjectProperty


class NumPad(Widget):
    value = NumericProperty(0)
    '''current value in the NumPad

    :data:`value` is a :class:`~kivy.properties.NumericProperty`
    '''

    max_value = NumericProperty(-1)
    '''
    maximum value accepted by the NumPad.

    :data:`max_value` is a :class:`~kivy.properties.NumericProperty`,
    default to -1, which means no limitation.
    '''

    nums = ObjectProperty(None)

    def __init__(self, popup, init_value=0, **kwargs):
        super(NumPad, self).__init__(**kwargs)
        self.value = min(self.value, self.max_value)

        for i in (
            range(7, 10) +
            range(4, 7) +
            range(1, 4) +
            ['del', '0', 'ret']
        ):
            b = Button(text=str(i))
            self.nums.add_widget(b)
            b.bind(on_release=self.button_callback)

        self.popup = popup

    def button_callback(self, button, *args):
        if button.text == 'del':
            self.value /= 10

        elif button.text == 'ret':
            self.popup.dismiss()

        else:
            self.value *= 10
            self.value += int(button.text)

            if self.max_value != -1:
                self.value = min(self.value, self.max_value)

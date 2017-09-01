'''
Toggle button
=============

.. image:: images/togglebutton.jpg
    :align: right

The :class:`ToggleButton` widget acts like a checkbox. When you touch or click
it, the state toggles between 'normal' and 'down' (as opposed to a
:class:`Button` that is only 'down' as long as it is pressed).

Toggle buttons can also be grouped to make radio buttons - only one button in
a group can be in a 'down' state. The group name can be a string or any other
hashable Python object::

    btn1 = ToggleButton(text='Male', group='sex',)
    btn2 = ToggleButton(text='Female', group='sex', state='down')
    btn3 = ToggleButton(text='Mixed', group='sex')

Only one of the buttons can be 'down'/checked at the same time.

To configure the ToggleButton, you can use the same properties that you can use
for a :class:`~kivy.uix.button.Button` class.

'''

__all__ = ('ToggleButton', )

from kivy.uix.button import Button
from kivy.uix.behaviors import ToggleButtonBehavior


class ToggleButton(ToggleButtonBehavior, Button):
    '''Toggle button class, see module documentation for more information.
    '''

    pass

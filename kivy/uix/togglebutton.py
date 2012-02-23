'''
Toggle button
=============

The :class:`ToggleButton` widget acts like a checkbox. When you touch/click it,
the state toggles between 'normal' and 'down' (opposed to a :class:`Button`
that is only 'down' as long as it is pressed).

Toggle buttons can also be grouped to make radio buttons - only one button in
a group can be in 'down' state. The group name can be a string or any other
hashable Python object ::

    btn1 = ToggleButton(text='Male', group='sex',)
    btn2 = ToggleButton(text='Female', group='sex', state='down')
    btn3 = ToggleButton(text='Mixed', group='sex')

Only one of the buttons can be 'down'/checked at the same time.

To configure the ToggleButton, you can use the same properties that you can use
for a Button class.

'''

__all__ = ('ToggleButton', )

from kivy.uix.button import Button
from kivy.properties import ObjectProperty


class ToggleButton(Button):
    '''Toggle button class, see module documentation for more information.
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the button. If None, no group will be used (button is
    independent). If specified, :data:`group` must be a hashable object, like
    a string. Only one button in a group can be in 'down' state.

    :data:`group` is a :class:`~kivy.properties.ObjectProperty`
    '''

    def __init__(self, **kwargs):
        self._previous_group = None
        super(ToggleButton, self).__init__(**kwargs)

    def on_group(self, *largs):
        groups = ToggleButton.__groups
        if self._previous_group:
            groups[self._previous_group].remove(self)
        group = self._previous_group = self.group
        if not group in groups:
            groups[group] = []
        groups[group].append(self)

    def _release_group(self, current):
        if self.group is None:
            return
        for widget in self.__groups[self.group]:
            if widget is current:
                continue
            widget.state = 'normal'

    def _do_press(self):
        self._release_group(self)
        self.state = 'normal' if self.state == 'down' else 'down'

    def _do_release(self):
        pass


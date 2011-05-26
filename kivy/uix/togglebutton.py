'''
Toggle button
=============

The toggle button act like a checkbox. When you touch it, his state will be
'down'. You need to touch it again to make his state to 'up'.

The toggle button is also able to handle group. Only one button can be pushed in
the same group. The group name can be a string, or any hashable Python object.
::

    btn1 = ToggleButton(text='Male', group='sex')
    btn2 = ToggleButton(text='Female', group='sex')
    btn3 = ToggleButton(text='Mixed', group='sex')

Only one of them could be checked.

'''

__all__ = ('ToggleButton', )

from kivy.uix.button import Button
from kivy.properties import ObjectProperty


class ToggleButton(Button):
    '''Toggle button class, see module documentation for more information.
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the button. If None, no group will be used.
    :data:`group` must be an hashable object, like a string.

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


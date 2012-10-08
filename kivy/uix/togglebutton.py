'''
Toggle button
=============

The :class:`ToggleButton` widget acts like a checkbox. When you touch/click it,
the state toggles between 'normal' and 'down' (opposed to a :class:`Button`
that is only 'down' as long as it is pressed).

Toggle buttons can also be grouped to make radio buttons - only one button in
a group can be in 'down' state. The group name can be a string or any other
hashable Python object::

    btn1 = ToggleButton(text='Male', group='sex',)
    btn2 = ToggleButton(text='Female', group='sex', state='down')
    btn3 = ToggleButton(text='Mixed', group='sex')

Only one of the buttons can be 'down'/checked at the same time.

To configure the ToggleButton, you can use the same properties that you can use
for a Button class.

'''

__all__ = ('ToggleButton', )

from weakref import ref
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
            group = groups[self._previous_group]
            for item in group[:]:
                if item() is self:
                    group.remove(item)
                    break
        group = self._previous_group = self.group
        if group not in groups:
            groups[group] = []
        r = ref(self, ToggleButton._clear_groups)
        groups[group].append(r)

    def _release_group(self, current):
        if self.group is None:
            return
        group = self.__groups[self.group]
        for item in group[:]:
            widget = item()
            if widget is None:
                group.remove(item)
            if widget is current:
                continue
            widget.state = 'normal'

    def _do_press(self):
        self._release_group(self)
        self.state = 'normal' if self.state == 'down' else 'down'

    def _do_release(self):
        pass

    @staticmethod
    def _clear_groups(wk):
        # auto flush the element when the weak reference have been deleted
        groups = ToggleButton.__groups
        for group in groups.values():
            if wk in group:
                group.remove(wk)
                break

    @staticmethod
    def get_widgets(groupname):
        '''Return the widgets contained in a specific group. If the group
        doesn't exist, an empty list will be returned.

        .. important::

            Always release the result of this method! In doubt, do::

                l = ToggleButton.get_widgets('mygroup')
                # do your job
                del l

        .. warning::

            It's possible that some widgets that you have previously deleted are
            still in the list. Garbage collector might need more elements before
            flushing it. The return of this method is informative, you've been
            warned!

        .. versionadded:: 1.3.0
        '''
        groups = ToggleButton.__groups
        if groupname not in groups:
            return []
        return [x() for x in groups[groupname] if x()][:]

    def set_ustate(self, st):
        self.state = 'down' if st=='down' else 'normal'

    def get_ustate(self):
        return self.state


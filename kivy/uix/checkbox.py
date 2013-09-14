'''
CheckBox
========

.. versionadded:: 1.4.0

.. image:: images/checkbox.png
    :align: right

:class:`CheckBox` is a specific two-state button that can be either checked or
unchecked. If the CheckBox is in a Group, it becomes a Radio button.
As with the :class:`~kivy.uix.togglebutton.ToggleButton`, only one Radio button
at a time can be selected when the :data:`CheckBox.group` is set.

An example usage::

    from kivy.uix.checkbox import CheckBox

    # ...

    def on_checkbox_active(checkbox, value):
        if value:
            print('The checkbox', checkbox, 'is active')
        else:
            print('The checkbox', checkbox, 'is inactive')

    checkbox = CheckBox()
    checkbox.bind(active=on_checkbox_active)
'''

__all__ = ('CheckBox', )

from weakref import ref
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, ObjectProperty


class CheckBox(Widget):
    '''CheckXox class, see module documentation for more information.
    '''

    active = BooleanProperty(False)
    '''Indicates if the switch is active or inactive.

    :data:`active` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the checkbox. If None, no group will be used (the checkbox is
    independent). If specified, the :data:`group` must be a hashable object
    such as a string. Only one checkbox in a group can be active.

    :data:`group` is an :class:`~kivy.properties.ObjectProperty` and defaults to
    None.
    '''

    def __init__(self, **kwargs):
        self._previous_group = None
        super(CheckBox, self).__init__(**kwargs)

    def on_group(self, *largs):
        groups = CheckBox.__groups
        if self._previous_group:
            group = groups[self._previous_group]
            for item in group[:]:
                if item() is self:
                    group.remove(item)
                    break
        group = self._previous_group = self.group
        if group not in groups:
            groups[group] = []
        r = ref(self, CheckBox._clear_groups)
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
            widget.active = False

    def _toggle_active(self):
        self._release_group(self)
        self.active = not self.active

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if self.disabled:
            return True
        self._toggle_active()
        return True

    @staticmethod
    def _clear_groups(wk):
        # auto flush the element when the weak reference have been deleted
        groups = CheckBox.__groups
        for group in list(groups.values()):
            if wk in group:
                group.remove(wk)
                break


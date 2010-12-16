'''
Toggle button:
'''

__all__ = ('ToggleButton', )

from kivy.uix.button import Button
from kivy.properties import StringProperty

class ToggleButton(Button):

    __groups = {}

    group = StringProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self._previous_group = None
        super(ToggleButton, self).__init__(**kwargs)

    def on_group(self, *largs):
        groups = ToggleButton.__groups
        if self._previous_group:
            groups.remove(self)
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


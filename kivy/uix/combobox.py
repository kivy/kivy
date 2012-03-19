#!/usr/bin/env python
'''
ComboBox
========

.. versionadded:: 1.1.2

A button that allows selecting a value from several options


.. warning::

    This is experimental and subject to change as long as this warning notice is
    present.
'''

from kivy.properties import ListProperty, ObjectProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout


class ComboBox(Button):
    '''ComboBox class, see module documentation for more information.

    :Events:
        `on_highlight`
            Fired when an entry is hovered by the touch / mouse.
    '''

    values = ListProperty([])
    '''Values that can be selected by the user, should be a list of strings
    '''

    select_class = ObjectProperty(Label)
    '''The class used to represent the options when displayed. The value will be
    passed the `text` and the `color` properties. It can be used to customize the apparence of the
    list.

    :data:`select_class` is an :class:`~kivy.properties.ObjectProperty`, default
    to `~kivy.uix.label.Label`.
    '''

    selected_color = ListProperty([1, 1, 1, 1])
    '''Text color when overed by the touch, in the format (r, g, b, a)

    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`, default     to [1, 1, 1, 1].
    '''

    current_index = NumericProperty(0)
    '''Index of the currently selected value. It can be used to
    initialize the widget with the default text.

    :data:`index` is a :class:`~kivy.properties.NumericProperty` default to 0.
    '''

    highlight_index = NumericProperty(None)
    '''Indicate the last hovered value.

    :data:`highlight_index` is a :class:`~kivy.properties.NumericProperty`,
    default to None.
    '''

    def __init__(self, **kwargs):
        super(ComboBox, self).__init__(**kwargs)
        if self.values:
            self.text = self.values[self.current_index]
        self.bind(current_index=self._update_text)

    def _update_text(self, *largs):
        self.text = str(self.values[self.current_index])

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            g = GridLayout(
                    cols=1,
                    x=self.x,
                    top=self.y,
                    col_default_width=self.width,
                    row_default_height=self.height)
            touch.ud['combobox_grid'] = g
            for v in self.values:
                g.add_widget(self.select_class(text=v, color=self.color))
            self.add_widget(g)
            return True

    def on_touch_move(self, touch, *args):
        if touch.grab_current is self:
            for i, l in enumerate(reversed(touch.ud['combobox_grid'].children)):
                if l.collide_point(*touch.pos):
                    l.color = self.selected_color
                    self.highlight_index = i
                else:
                    l.color = self.color

    def on_touch_up(self, touch, *args):
        if touch.grab_current is self:
            touch.ungrab(self)
            for i, l in enumerate(reversed(touch.ud['combobox_grid'].children)):
                if l.collide_point(*touch.pos):
                    self.current_index = i
                    self.remove_widget(touch.ud['combobox_grid'])
                    return True
            self.remove_widget(touch.ud['combobox_grid'])

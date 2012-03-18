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

from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout

class ComboBox(Button):
    values = ListProperty([])
    '''Values that can be selected by the user, should be a list of strings
    '''

    select_class = ObjectProperty(Label)
    '''The class used to represent the options when displayed, the value will be
    passed to the `text` property. Can be used to customize the apparence of the
    list.

    :data:`select_class` is an :class:`~kivy.properties.ObjectProperty`, default
    to `~kivy.uix.label.Label`.
    '''

    selected_color = ListProperty([1, 1, 1, 1])
    '''Text color when overed by the touch, in the format (r, g, b, a)

    :data:`color` is a :class:`~kivy.properties.ListProperty`, default to [1, 1,
    1, 1].
    '''

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
        if touch.grab_current == self:
            for l in touch.ud['combobox_grid'].children:
                if hasattr(l, 'color'):
                    if l.collide_point(*touch.pos):
                        l.color = self.selected_color
                    else:
                        l.color = self.color

    def on_touch_up(self, touch, *args):
        if touch.grab_current == self:
            for l in touch.ud['combobox_grid'].children:
                if l.collide_point(*touch.pos):
                    self.text = l.text
                    self.remove_widget(touch.ud['combobox_grid'])
                    return True
            self.remove_widget(touch.ud['combobox_grid'])

def printf(*args):
    print args

class ComboBoxTest(App):
    def build(self):
        f = FloatLayout()
        c = ComboBox(
                values=['a', 'b', 'c'],
                pos_hint={'center_x':.5, 'center_y': .5},
                size_hint=(None, None),
                size=(200, 20),
                selected_color=(1, .2, .2 , 1))

        c.bind(text=printf)
        f.add_widget(c)
        return f

if __name__ == '__main__':
    ComboBoxTest().run()


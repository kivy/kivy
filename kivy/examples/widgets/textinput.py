'''
Textinput tests
===============

This test is used to demonstrate virtual keyboard according to current
configuration.
Run this test as::

    # use dock virtual keyboard (one instance)
    python textinput.py -c kivy:keyboard_mode:dock
    # use multi users virtual keyboard (multiples instance)
    python textinput.py -c kivy:keyboard_mode:multi
    # use system keyboard (one instance)
    python textinput.py -c kivy:keyboard_mode:system
    # use automatic detection from current platform
    python textinput.py -c kivy:keyboard_mode:

'''

import kivy
kivy.require('1.0.8')

from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.config import Config
from kivy.base import runTouchApp

if __name__ == '__main__':

    root = FloatLayout()

    # create a button to release everything
    def release_all_keyboard(*l):
        Window.release_all_keyboards()
    btn = Button(text='Release\nall\nkeyboards', size_hint=(None, None),
            halign='center')
    btn.bind(on_release=release_all_keyboard)
    root.add_widget(btn)

    # show current configuration
    lbl = 'Configuration keyboard_mode is %r, keyboard_layout is %r' % (
        Config.get('kivy', 'keyboard_mode'),
        Config.get('kivy', 'keyboard_layout'))
    label = Label(text=lbl, size_hint_y=None, height=50, pos_hint={'top': 1})
    root.add_widget(label)

    s = Scatter(size_hint=(None, None), pos=(300, 300))
    s.add_widget(TextInput(size_hint=(None, None), size=(100, 50)))
    root.add_widget(s)

    s = Scatter(size_hint=(None, None), pos=(400, 300), rotation=45)
    s.add_widget(TextInput(size_hint=(None, None), size=(100, 50)))
    root.add_widget(s)

    runTouchApp(root)

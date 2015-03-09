# -*- coding: utf-8 -*-

import os
import kivy
kivy.require('1.8.0')
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.actionbar import ActionBar
from kivy.properties import ObjectProperty


class RootWidget(BoxLayout):

    '''Create a controller that receives a custom widget from the kv lang file. Add an action to be called from a kv file.'''

    container = ObjectProperty(None)


class EzsApp(App):

    '''This is the app itself'''

    path = os.path.abspath(os.path.dirname("."))
    error = False

    def build(self):
        '''This method loads the root.kv file automatically

        :rtype: none
        '''

        self.root = Builder.load_file(os.path.join(self.path, 'kv', 'root.kv'))

        return self.root

    def next_screen(self, screen):
        '''Clear container and load the given screen object from file in kv folder

        :param screen: name of the screen object made from the loaded .kv file
        :type screen: str
        :rtype: none
    '''

        filename = screen + '.kv'

        setattr(self, screen, Builder.unload_file(
            os.path.join(self.path, 'kv', filename)))
        setattr(self, screen, Builder.load_file(
            os.path.join(self.path, 'kv', filename)))
        self.root.container.clear_widgets()
        self.root.container.add_widget(getattr(self, screen))


if __name__ == '__main__':
    '''Start the application'''

    EZS = EzsApp()
    EZS.run()

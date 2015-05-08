# -*- coding: utf-8 -*-
'''
Container Example
==============

This example shows how to add a container to our screen.
A container is simply an empty place on the screen which
could be filled with any other content from a .kv file.
'''
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

import os
import kivy
kivy.require('1.8.0')


class RootWidget(BoxLayout):
    '''Create a controller that receives a custom widget from the kv lang file.
    Add an action to be called from a kv file.
    '''

    container = ObjectProperty(None)


class EzsApp(App):

    '''This is the app itself'''
    # setting the path of our directory
    path = os.path.abspath(os.path.dirname("."))
    error = False

    def build(self):
        '''This method loads the root.kv file automatically

        :rtype: none
        '''
        # loading the content of root.kv
        self.root = Builder.load_file(os.path.join(self.path, 'kv', 'root.kv'))

        return self.root

    def next_screen(self, screen):
        '''Clear container and load the given screen object from file in kv
        folder.

        :param screen: name of the screen object made from the loaded .kv file
        :type screen: str
        :rtype: none
    '''

        filename = screen + '.kv'
        # unload the content of the .kv file
        # reason: it could have data form previous calls
        setattr(self, screen, Builder.unload_file(
            os.path.join(self.path, 'kv', filename)))
        # load the content of the .kv file
        setattr(self, screen, Builder.load_file(
            os.path.join(self.path, 'kv', filename)))
        # clear the container
        self.root.container.clear_widgets()
        # add the content of the .kv file to the container
        self.root.container.add_widget(getattr(self, screen))


if __name__ == '__main__':
    '''Start the application'''

    EZS = EzsApp()
    EZS.run()

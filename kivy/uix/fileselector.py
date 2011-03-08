#!/usr/bin/env python
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.config import Config

from kivy.app import App
from os import listdir
from os import sep
from os import getcwd
from os.path import isdir
from os.path import join

from time import sleep

__all__ = ('FileSelectorException', 'FileSelector')


class FileSelectorException(Exception):
    '''Exception in the manipulation of FileSelector widget.
    '''
    pass


class FileItem(Button):
    '''
    object representing a file that one can select using FileSelector widget
    '''

    def __init__(self, text, callback, color):
        '''
        '''
        Button.__init__(self, text=text, color=color)
        self.text_size = (100, None)
        self.name = text
        self.callback = callback
        self.touched = False
        self.height = 50

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y) and touch.is_double_tap:
            self.callback(self.text)


class FileSelector(Scatter):
    '''FileSelector widget
    '''

    def __init__(self, callback, path=getcwd()):
        ''' parameter 'callback' must be a callable accepting one parameter to
        pass the filename selected, optional 'path' argument is the path where
        the FileSelector widget start browsing.
        '''
        Scatter.__init__(self)
        self.do_rotation = False
        self.callback = callback
        self.path = getcwd()
        self.grid = GridLayout(cols=6, spacing=5)
        self.sort = self.filetype_sort

        self.box = BoxLayout(orientation='vertical', spacing=20,
                uniform_height=True, uniform_width=True)
        self.label = Label(text=self.path)
        #self.label.top = 0
        #self.label.x = 0
        #self.label.height = 20

        self.box.add_widget(self.label)
        self.box.add_widget(self.grid)
        self.add_widget(self.box)
        self.update_display()

    def alpha_sort(self, stringlist):
        '''this is an alphanumeric sort, intended to be used by fileselector
        '''
        return sorted(stringlist)

    def filetype_sort(self, stringlist):
        '''this is an sort on file type, intended to be used by fileselector
        '''
        #TODO
        return sorted(stringlist, key=lambda f: (isdir(join(self.path, f)) and
        'A' or 'B') + f.lower())

    def select(self, name):
        ''' call the callback given to the widget, with the full pathname to
        the selected file.
        '''
        self.callback(join(self.path, name))

    def cd(self, name):
        ''' change widget current directory to the selected directory.
        '''
        if name == '..':
            self.path = sep.join(self.path.split('/')[:-1]) or '/'
        else:
            self.path += sep + name
        self.update_display()

    def update_display(self):
        ''' recreate the set of widgets to show directories and files of the
        current working directory.
        '''
        self.label.text = self.path
        self.grid.clear_widgets()
        for f in self.ls():
            if isdir(join(self.path, f)):
                c = self.cd
                color = [1, 1, 0]
            else:
                c = self.select
                color = [1, 1, 1]

            self.grid.add_widget(FileItem(text=f, callback=c, color=color))
        self.box.update_minimum_size()
        self.box.top = Config.getint('graphics', 'height')

    def ls(self):
        ''' return the set of files to display
        '''
        return reversed((['..', ] + self.sort(listdir(self.path))))


class FSDemo(App):
    '''Example application
    '''

    def callback(self, filename):
        print filename
        self.stop()

    def build(self):
        return FileSelector(self.callback)

if __name__ in ('__main__', '__android__'):
    FSDemo().run()

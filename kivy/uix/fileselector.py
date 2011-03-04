#!/usr/bin/env python
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty

from kivy.app import App
from os import listdir
from os.path import isdir
from os.path import join

__all__ = ('FileSelectorException', 'FileSelector')


class FileSelectorException(Exception):
    '''Exception in the manipulation of FileSelector widget.
    '''
    pass


def alpha_sort(stringlist):
    '''this is an alphanumeric sort, intended to be used by fileselector
    '''
    return sorted(stringlist)


def filetype_sort(stringlist):
    '''this is an sort on file type, intended to be used by fileselector
    '''
    #TODO
    raise NotImplementedError


class File(Button):
    '''
    object representing a file that one can select using FileSelector widget
    '''

    def __init__(self, text, callback):
        '''
        '''
        Button.__init__(self, text=text)
        self.name = text
        self.callback = callback

    def on_touch_down(self, touch):
        #print "tap"
        #if touch.is_double_tap:
            #print "double tap"
            print self.text
            print self.name
            self.callback(self.text)


class FileSelector(Widget):
    '''FileSelector widget
    '''

    callback = ObjectProperty(None)

    def __init__(self, *largs):
        '''
        '''
        Widget.__init__(self)
        self.path = '.'
        self.grid = GridLayout(rows=(self.height-50)/20)
        self.add_widget(self.grid)
        self.sort = alpha_sort
        self.update_display()

    def select(self, name):
        '''
        '''
        self.callback(join(self.path, name))

    def cd(self, name):
        '''
        '''
        print join(self.path, name)
        self.path += os.sep + name
        self.update_display()

    def update_display(self):
        '''
        '''
        self.grid.clear_widgets()
        for f in self.ls():
            if isdir(join(self.path, f)):
                c = self.cd
            else:
                c = self.select

            button = File(text=f, callback=c)
            self.grid.add_widget(button)

    def ls(self):
        '''
        '''
        return self.sort(listdir(self.path))


class FSDemo(App):
    '''Example application
    '''

    def callback(self, filename):
        print filename
        self.stop()

    def build(self):
        return FileSelector(self.callback)

if __name__ == '__main__':
    FSDemo().run()

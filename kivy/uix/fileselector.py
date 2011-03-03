#!/usr/bin/env python
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

from kivy.app import App
from os import listdir
from os.path import isdir

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


class File(object):
    '''
    object representing a file that one can select using FileSelector widget
    '''

    def __init__(self, name):
        self.name = name


class FileSelector(Widget):
    '''FileSelector widget
    '''

    def default_callback(self, filename):
        print filename

    def __init__(self, *largs):
        Widget.__init__(self)
        self.path = '.'
        self.grid = GridLayout(rows=(self.height-50)/20)
        self.add_widget(self.grid)
        self.sort = alpha_sort
        self.update_display()

        if 'callback' in largs:
            self.callback = largs['callback']
        else:
            self.callback = self.default_callback

    def selecter(self):

        def select(instance):
            if isdir(self.path+instance.name):
                self.path += instance.name
                self.update_display()
            else:
                self.callback(instance.name)
        return select

    def update_display(self):
        self.grid.clear_widgets()
        for f in self.ls():
            select = self.selecter()
            button = Button(text=f.name, on_press=self.selecter())
            self.grid.add_widget(button)

    def ls(self):
        return (File(name) for name in self.sort(listdir(self.path)))


class FSDemo(App):
    '''Example application
    '''

    def build(self):
        return FileSelector()

if __name__ == '__main__':
    FSDemo().run()

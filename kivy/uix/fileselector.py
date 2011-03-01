#!/usr/bin/env python
from kivy.widget import Widget
from kivy.button import Button
from kivy.label import Label
from kivy.uix.gridlayout import GridLayout

from os import listdir
from os.path import isdir


class FileSelectorException(Exception):
    pass


def alpha_sort(stringlist):
    return sorted(stringlist)


def filetype_sort(stringlist):
    #TODO
    raise NotImplementedError


class file(object):

    def __init__(self, name):
        self.name = name

    def call(self):
        pass


class FileSelector(Widget):

    def __init__(self, *largs):
        Widget.__init__(self)
        self.cd = '.'
        self.grid = GridLayout(rows=(self.height-50)/20)
        self.add_widget(self.grid)
        self.sort = alpha_sort

        def cd(self, path):
            if isdir(path):
                self.path = path
                self.update_display()
            else:
                raise FileSelectorException("invalid path "+path)

        def update_display(self):
            self.grid.clear_widgets()
            for f in self.ls():
                button = Button(text=f, on_press=)
                self.grid.add_widget(button)

        def ls(self):
            return self.sort(listdir(self.path))


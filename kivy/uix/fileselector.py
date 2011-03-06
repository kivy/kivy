#!/usr/bin/env python
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty

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
        self.touched = False
        self.height = 20

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if self.touched:
                return
            else:
                self.touched = True
                print "tap " + self.name
                if touch.is_double_tap:
                    print "double tap"
                    self.callback(self.text)

    def on_touch_up(self, touch):
        self.touched = False


class FileSelector(Widget):
    '''FileSelector widget
    '''

    def __init__(self, callback, path=getcwd()):
        '''
        '''
        Widget.__init__(self)
        self.callback = callback
        self.path = getcwd()
        self.grid = GridLayout(cols=6)
        self.add_widget(self.grid)
        self.sort = alpha_sort
        self.update_display()

    def select(self, name):
        ''' call the callback given to the widget, with the full pathname to
        the selected file.
        '''
        self.callback(join(self.path, name))

    def cd(self, name):
        ''' change widget current directory to the selected directory.
        '''
        if name == '..':
            self.path = sep.join(self.path.split('/')[:-1])
        else:
            self.path += sep + name
        self.update_display()

    def update_display(self):
        ''' recreate the set of widgets to show directories and files of the
        current working directory.
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
        ''' return the set of files to display
        '''
        return reversed(
                (
                    self.path != '/' and ['..', ] or '/') +
                    self.sort(listdir(self.path)))

    def on_touch_move(self, touch):
        print touch.dpos
        self.grid.top += touch.dsy * 1000
        self.grid.x += touch.dsx * 1000


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

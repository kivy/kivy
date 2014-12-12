'''
Application Suite
=================

Explore how applications start.   Starts applications one after another, waiting for
each to be closed first.
'''

import sys
import re
from random import choice

import kivy
kivy.require('1.8.0')  # Minimum API as 1.8 is when kv_directory became part of app.
from kivy.app import App
from kivy.uix.button import Button
from kivy.lang import Builder

class TestBuildApp(App):
    """ Use build() function to return a widget. """
    def build(self):
        """   Build called by kivy when an App is started.
              Called after trying to load a .kv file.
              Returns a new Button as a root widget.
              """
        print "** inside build()"
        return Button(text='hello from TestBuildApp')

class TestKVFileApp(App):
    """ Empty class, but name used to find .kv file.
    The filename is the lowercase version of the class, i.e.,
    'testkvfileapp.kv'.  If not found, it strips off the final 'app', i.e.,
    'testkvfile.kv'.

    If not file is found, and no other method sets the self.root, the program will
    run with an empty screen. """
    pass

class TestKVDirApp(App):
    """ Empty class except for setting class variable kv_directory.
    This directory sets the directory in which to search for the .kv file.
    The name of the kv file is still governed by the class name and the .kv
    file should still have one root widget. """
    kv_directory = 'app_suite_data'

class TestKVStringApp(App):
    """ Use a build() function and use the kivy.lang.Builder function to parse up a
        Kivy language string.  """
    def build(self):
        """   Called by kivy run().  """
        print "** inside build()"
        widget = Builder.load_string("Button:\n  text: 'hello from TestKVStringApp'")
        print "** widget built"
        return widget

def print_class(class_name):
    """ Read this file and print the section with the class name specified.) """
    filename = sys.argv[0]
    with open(filename) as f:
        data = f.read()
        regex = "^(class " + class_name + "\\b.*?)^\\S"
        match = re.search(regex, data, flags=re.MULTILINE|re.DOTALL)
        if match:
            print match.group(1)

# the __name__ idiom executes when run from command line but not from import.
if __name__ == '__main__':
    dash = "-" * 40

    arg = sys.argv[1][0].lower() if len(sys.argv) > 1 else "h"
    print dash

    if arg == 'r':
        arg = choice('bfds')

    if arg == 'b':
        print_class("TestBuildApp")
        TestBuildApp().run()
    elif arg == 'f':
        print_class("TestKVFileApp")
        TestKVFileApp().run()
    elif arg == 'd':
        print_class("TestKVDirApp")
        TestKVDirApp().run()
    elif arg == 's':
        print_class("TestKVStringApp")
        TestKVStringApp().run()
    else:   # help
        print """
This demo runs different application windows based on a command line argument.

Try using one of these:
   b - Use build() method to return a widget
   d - Use a kv file from a different directory
   f - Use a kv file with the widget object
   s - Use a kiva language string to create the widget.
   r - pick one of the demos at random.

   h - show this help message.

   After closing the application window, this program will exit.   While the run() method
   does return, kivy cannot run another application.
 """

    print dash
    print "This program is gratified to be of use."

'''
Application from a .kv in a Template Directory
==============================================

This example shows how you can change the directory for the .kv file. You
should see "Hello from template1/test.ky" as a button.

As kivy instantiates the TestApp subclass of App, the variable kv_directory
is set. Kivy then implicitly searches for a .kv file matching the name
of the subclass in that directory, finding the file template1/test.kv. That
file contains the root widget.


'''

import kivy
kivy.require('1.0.7')

from kivy.app import App


class TestApp(App):
    kv_directory = 'template1'


if __name__ == '__main__':
    TestApp().run()

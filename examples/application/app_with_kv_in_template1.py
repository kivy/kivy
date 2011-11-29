'''
Application from a .kv
======================

The root application is created from the corresponding .kv. Check the test.kv
file to see what will be the root widget.
This example show how you can change the directory where the .kv live.
'''

import kivy
kivy.require('1.0.7')

from kivy.app import App


class TestApp(App):
    kv_directory = 'template1'

if __name__ == '__main__':
    TestApp().run()

'''
Application from a .kv
======================

The root application is created from the corresponding .kv. Check the test.kv
file to see what will be the root widget.
'''

import kivy
kivy.require('1.0.7')

from kivy.app import App


class TestApp(App):
    pass

if __name__ == '__main__':
    TestApp().run()

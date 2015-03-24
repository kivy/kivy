'''
The use of id in .kv
==================================

This small example shows how to refer from one widget
on an other widget within .kv
'''
from kivy.app import App

import kivy
kivy.require('1.8.0')


class TestApp(App):
    pass

if __name__ == '__main__':
    TestApp().run()

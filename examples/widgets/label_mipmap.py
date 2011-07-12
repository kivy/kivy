'''
Label mipmap
============

This show how to create a mipmapped label, and the visual difference between a
non mipmapped and mipmapped label.
'''

import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.scatter import ScatterPlane
from kivy.uix.label import Label

class LabelMipmapTest(App):
    def build(self):
        s = ScatterPlane(scale=.5)
        l1 = Label(text='Kivy rulz', font_size=98, pos=(400, 100), mipmap=True)
        l2 = Label(text='Kivy rulz', font_size=98, pos=(400, 328))
        s.add_widget(l1)
        s.add_widget(l2)
        return s

if __name__ in ('__main__', '__android__'):
    LabelMipmapTest().run()

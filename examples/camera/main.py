'''
Camera Example
==============

This example demonstrates a simple use of the camera. It shows a window with
a buttoned labelled 'play' to turn the camera on and off. Note that
not finding a camera, perhaps because gstreamer is not installed, will
throw an exception during the kv language processing.

'''

# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
import time
Builder.load_string('''
<CameraClick>:
    BoxLayout:
        orientation: 'vertical'
        Camera:
            id: camera
            resolution: (640, 480)
            play: False
        ToggleButton:
            text: 'Play'
            on_press: camera.play = not camera.play
            size_hint_y: None
            height: '48dp'
        Button:
            text: 'Capture'
            size_hint_y: None
            height: '48dp'
            on_press: root.click_pic()
'''
)
class CameraClick(BoxLayout):
    def click_pic(self):
        '''
        Function to capture the images and give them the names 
        according to their captured time and date.
        '''
        camera = self.ids['camera']
        timestr = time.strftime("%d-%m-%Y_%H:%M:%S")
        camera.export_to_png("IMG_" + timestr)
        print "Captured"
        

class TestCamera(App):

    def build(self):
        return CameraClick()


TestCamera().run()

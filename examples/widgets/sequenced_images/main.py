import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from uix.custom_button import AnimatedButton
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.properties import ObjectProperty
from kivy.core import window


class gifScatter(Scatter):
    def __init__(self, **kwargs):
        super(gifScatter, self).__init__()


class zipScatter(Scatter):
    def __init__(self, **kwargs):
        super(zipScatter, self).__init__()


class jpgScatter(Scatter):
    def __init__(self, **kwargs):
        super(jpgScatter, self).__init__()


class Right_Frame(GridLayout):

    currentObj = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Right_Frame, self).__init__()

    def on_value(self, *l):
        if self.currentObj:
            if abs(l[1]) <= 0 :
                self.currentObj.anim_delay = -1
                l[2].text = 'Animation speed: %f FPS' %0
            else:
                self.currentObj.anim_delay = 1/l[1]
                l[2].text = 'Animation speed: %f FPS' %(1/self.currentObj.anim_delay)
        else:
            l[0].max  = 0
            l[2].text = 'No Image selected'


class mainclass(FloatLayout):

    currentObj = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(mainclass, self).__init__()

        # initialize variables
        self.sign = .10

        #setup Layouts
        layout            = GridLayout( size_hint = (1, 1), cols = 3, rows = 1)
        left_frame        = GridLayout( size_hint = (.25, 1), cols = 1)
        client_frame      = FloatLayout( size_hint = (1, 1))
        self.right_frame  = Right_Frame()

        #setup buttons in left frame
        but_load_gif     = AnimatedButton(text = 'load gif', halign = 'center')
        but_load_zip_png = AnimatedButton(text = 'load zipped\n png/s', halign = 'center')
        but_load_zip_jpg = AnimatedButton(text = 'load zipped\n jpg/s', halign = 'center')
        but_animated     = AnimatedButton(text = 'animated button\n'+\
            'made using\nSequenced Images\n press to animate', halign = 'center',\
            background_normal = 'data/images/button_white.png',\
            background_down   = 'data/images/button_white_animated.zip')
        but_animated_normal   = AnimatedButton(text = 'borderless\n'+\
            'animated button\npress to stop', halign = 'center',\
            background_down   = 'data/images/button_white.png',\
            background_normal = 'data/images/button_white_animated.zip')
        but_animated_borderless = AnimatedButton(text = 'Borderless',\
            background_normal = 'data/images/info.png',\
            background_down   = 'data/images/info.zip', halign = 'center')
        but_animated_bordered = AnimatedButton(text = 'With Border',\
            background_normal = 'data/images/info.png',\
            background_down   = 'data/images/info.zip', halign = 'center')

        #Handle button press/release
        def load_images(*l):

            if l[0].text == 'load gif' or l[0].text == 'load gif\n from cache':
                l[0].text = 'load gif\n from cache'
                sctr = gifScatter()
            if l[0].text == 'load zipped\n png/s' or\
                l[0].text == 'load zipped\n png/s from cache':
                l[0].text = 'load zipped\n png/s from cache'
                sctr = zipScatter()
            if l[0].text == 'load zipped\n jpg/s' or l[0].text == 'load zipped\n jpg/s from cache':
                l[0].text = 'load zipped\n jpg/s from cache'
                sctr = jpgScatter()

            client_frame.add_widget(sctr, 1)

            #position scatter
            sctr.pos = (240 + self.sign, 200+ self.sign )
            self.sign += 10
            if self.sign >200:
                self.sign = 10
                sctr.pos = (300, 200 -  self.sign)


        #bind function on on_release
        but_load_gif.bind(on_release = load_images)
        but_load_zip_png.bind(on_release = load_images)
        but_load_zip_jpg.bind(on_release = load_images)

        #add widgets to left frame
        left_frame.add_widget(but_load_gif)
        left_frame.add_widget(but_load_zip_png)
        left_frame.add_widget(but_load_zip_jpg)
        left_frame.add_widget(but_animated)
        left_frame.add_widget(but_animated_normal)
        left_frame.add_widget(but_animated_borderless)
        left_frame.add_widget(but_animated_bordered)

        #set/remove border for borderless widgets (16,16,16,16) by default
        but_animated_normal.border = but_animated_borderless.border = (0,0,0,0)

        #add widgets to the main layout
        layout.add_widget(left_frame)
        layout.add_widget(client_frame)
        layout.add_widget(self.right_frame)

        #add main layout to root
        self.add_widget(layout)

    def on_currentObj(self, *l):
        self.right_frame.currentObj = self.currentObj


class mainApp(App):

    def build(self):
        upl = mainclass()
        upl.size_hint = (1,1)
        upl.pos_hint = {'top':0, 'right':1}
        return upl


if __name__ == '__main__':
    mainApp().run()

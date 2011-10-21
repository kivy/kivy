import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from uix.custom_button import AnimatedButton
from kivy.uix.image import Image

class mainclass(FloatLayout):

    def __init__(self, **kwargs):
	super(mainclass, self).__init__()
        layout = GridLayout( size_hint = (1, 1), rows = 5)
	
	but_load_gif = AnimatedButton(text = 'load gif')
	#but_load_gif_from_cache = AnimatedButton(text = 'load gif from cache')
	but_load_zip = AnimatedButton(text = 'load zipped png/s')
	#but_load_zip_from_cache = AnimatedButton(text = 'load zipped png/s from cache')
	but_animated = AnimatedButton(text = 'animated button \npress to animate', background_normal = 'data/images/button_white.png', background_down = 'data/images/button_white_animated.zip')

	def load_images(*l):
            if l[0].text == 'load gif' or l[0].text == 'load gif from cache':
                l[0].text = 'load gif from cache'
                layout.add_widget(Image (source = 'data/images/busy-stick-figures-animated.gif', allow_stretch = True ))
	    if l[0].text == 'load zipped png/s' or l[0].text == 'load zipped png/s from cache':
                l[0].text = 'load zipped png/s from cache'
                layout.add_widget(Image (source = 'data/images/RingGreen.zip' , allow_stretch = True))
	
	but_load_gif.bind(on_release = load_images)
	#but_load_gif_from_cache.bind(on_release = load_images)
	but_load_zip.bind(on_release = load_images)
	#but_load_zip_from_cache.bind(on_release = load_images)

	layout.add_widget(but_load_gif)
	#layout.add_widget(but_load_gif_from_cache)
        layout.add_widget(but_load_zip)
	#layout.add_widget(but_load_zip_from_cache)
	layout.add_widget(but_animated)

	self.add_widget(layout)
	

class mainApp(App):

    def build(self):
	upl = mainclass()
	upl.size_hint = (1,1)
	upl.pos_hint = {'top':0, 'right':1}
	return upl


if __name__ in ('__main__', '__android__'):
	    mainApp().run()

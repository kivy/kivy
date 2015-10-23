import kivy
from select import select
kivy.require('1.8.0')
from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.logger import Logger

from vlcvideoview import VlcVideoView
VlcVideoView.VlcLibOptions.append('-vvv')
VlcVideoView.VlcLibOptions.append('--network-caching=100')

from mediastore import query_storage_video
	
VIDEO_TEST_URLs = [
		'rtsp://184.72.239.149/vod/mp4:BigBuckBunny_115k.mov',
]

class VlcExampleApp(App):
	source = StringProperty(VIDEO_TEST_URLs[0])
	def build(self):
		Logger.info('VlcExampleApp: building...')

		self._medialist_idx = 0

		self._box = box = FloatLayout()

		self._video = VlcVideoView(
					source=self.source,
					pos_hint={'x':0.0, 'y':0.1},
					size_hint=(1.0, 0.9),
		)
		self._video.bind(state=self.on_video_state)
		self._video.bind(eos=self.on_video_eos)
		box.add_widget(self._video)

		self._btn_play = Button(
					text = '>',
					pos_hint={'x':0.0, 'y':0.0},
					size_hint=(0.1, 0.1)
		)
		self._btn_play.bind(on_press=self.on_btn_play_press)
		box.add_widget(self._btn_play)

		self._edt = TextInput(
					text = self.source,
					pos_hint={'x':0.1, 'y':0.0},
					size_hint=(0.8, 0.1)
		)
		self._edt.bind(text=self.setter('source'))
		box.add_widget(self._edt)

		self._btn_next = Button(
					text = '>>',
					pos_hint={'x':0.9, 'y':0.0},
					size_hint=(0.1, 0.1)
		)
		self._btn_next.bind(on_press=self.on_btn_next_press)
		box.add_widget(self._btn_next)
		
		self._progress = None

		self._video.bind(loaded=self.on_video_loaded)
# 		self.bind(source=self.on_source)

		return box	

	def _show_progress(self, seekable):
		Logger.info('VlcExampleApp: showing progress {}'.format(seekable))
		cls = Slider if seekable else ProgressBar
		self._progress = cls(
					pos_hint={'x':0.0, 'y':0.1},
					size_hint=(1.0, None),
					opacity = 0.5,
					max = self._video.duration,
					value = self._video.position,
					on_touch_down = self.do_seek,
					on_touch_move = self.do_seek,
					on_touch_up = self.do_seek,
		)
		self._video.bind(duration=self._progress.setter('max'))
		self._video.bind(position=self._progress.setter('value'))
		self._box.add_widget(self._progress)
		
	def _hide_progress(self):
		if self._progress:
			Logger.info('VlcExampleApp: hiding progress')
			self._video.unbind(duration=self._progress.setter('max'))
			self._video.unbind(position=self._progress.setter('value'))
			self._box.remove_widget(self._progress)
			self._progress = None

	def on_source(self, instance, value):
		Logger.info('VlcExampleApp: on_source: %s'%value)
		self._video.source = value 
		self._video.state = 'stop'
		
	def on_btn_play_press(self, instance):
		Logger.info('VLC Example: on_btn_play_press')
		if self._video.state == 'play':
			self._video.state = 'pause'
		else:
			self._video.state = 'play'

	def on_btn_next_press(self, instance):
		Logger.info('VLC Example: on_btn_next_press')
		self._medialist_idx = self._medialist_idx + 1 
		if self._medialist_idx < len(VIDEO_TEST_URLs):
			all_medias = VIDEO_TEST_URLs
		else:
			all_medias = VIDEO_TEST_URLs + query_storage_video()
		self._medialist_idx = self._medialist_idx%len(all_medias)
		self._edt.text = all_medias[self._medialist_idx]

	def on_video_loaded(self, instance, value):
		Logger.info('VLC Example: on_video_loaded {}'.format(value))
		if value and self._video.duration > 0:
			self._video.state = 'play'
			self._show_progress(False)
		else:
			self._hide_progress()

	def on_video_state(self, instance, value):
		Logger.info('VLC Example: on_video_state {}'.format(value))
		self._btn_play.text = {'play':  '||', 'pause': '|>', 'stop':  '>'}[value]
		for w in (self._btn_next, self._edt):
			w.disabled = (value == 'play')

	def on_video_eos(self, instance, value):
		Logger.info('VLC Example: on_video_eos {}'.format(value))
		if value:
			self._video.state = 'stop'
			
	def do_seek(self, *largs):
		self._video.seek(self._progress.value_normalized)

def run():
	a = VlcExampleApp()
	a.run()
	
if __name__ == '__main__':
	run()

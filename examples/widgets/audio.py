from kivy.uix.button import Button
from kivy.app import App
from kivy.core.audio import SoundLoader
from os.path import dirname, join


class SoundApp(App):
    def build(self):
        curdir = dirname(__file__)
        # Taken from http://www.jamendo.com/en/album/91153
        fn = join(curdir, 'beginning_of_anxiety.mp3')
        sound = SoundLoader.load(filename=fn)
        text = 'Audio Unavailable'
        if sound:
            text = 'Play'

        def callback(btn, *args):
            if btn.text == 'Play':
                sound.play()
                btn.text = 'Stop'
            elif btn.text == 'Stop':
                sound.stop()
                btn.text = 'Play'

        btn = Button(text=text)
        btn.bind(on_release=callback)

        return btn


SoundApp().run()


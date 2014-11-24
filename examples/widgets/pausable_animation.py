import kivy
from kivy.animation import Animation
from kivy.app import App
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from functools import partial


class TestPAuseAnimationApp(App):
    def animate(self, instance):
        def plop(*args):
            print args
        animation = Animation(x=Window.width / 2, y=Window.height / 2,
                              duration=3)
        animation += Animation(x=0, y=0, duration=3)
        animation.repeat = True
        animation.bind(on_pause=partial(plop, 'pause'))
        animation.start(instance)
        return animation

    def pauseAnimation(self, animation, button):
        #toggle the pause property
        pause = not animation.paused
        animation.pause(pause)

    def pauseAll(self, *args):
        self.paused = not self.paused
        Animation.pause_all(self.paused)

    def build(self):
        f = FloatLayout()
        self.paused = False
        b1 = Button(size_hint=(None, None), text='Button1')
        a = self.animate(b1)
        b1.bind(on_press=partial(self.pauseAnimation, a))
        b2 = Button(size_hint=(None, None), text='pause all')
        b2.bind(on_press=self.pauseAll)
        b3 = Button(size_hint=(None, None), text='Button3')
        a = self.animate(b3)
        b3.bind(on_press=partial(self.pauseAnimation, a))
        f.add_widget(b1)
        f.add_widget(b2)
        f.add_widget(b3)
        return f

if __name__ == '__main__':
    TestPAuseAnimationApp().run()

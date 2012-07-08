from kivy.event import EventDispatcher
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty, \
        NumericProperty, ListProperty, OptionProperty
from kivy.animation import Animation
from kivy.logger import Logger
from kivy.uix.scatter import Scatter
from kivy.lang import Builder

Builder.load_string('''
<RelativeFloatLayout>:
    do_translation: False
    do_rotation: False
    do_scale: False
''')

class RelativeFloatLayout(Scatter):
    content = ObjectProperty()
    def __init__(self, **kw):
        self.content = FloatLayout()
        super(RelativeFloatLayout, self).__init__(**kw)
        super(RelativeFloatLayout, self).add_widget(self.content)
        self.bind(size=self.update_size)

    def update_size(self, instance, size):
        self.content.size = size

    def add_widget(self, *l):
        self.content.add_widget(*l)

    def remove_widget(self, *l):
        self.content.remove_widget(*l)


class Screen(RelativeFloatLayout):
    name = StringProperty('')
    manager = ObjectProperty()
    transition_alpha = NumericProperty(0.)
    transition_state = OptionProperty('out', options=('in', 'out'))

    def __repr__(self):
        return '<Screen name=%r>' % self.name


class Transition(EventDispatcher):
    screen_out = ObjectProperty()
    screen_in = ObjectProperty()
    duration = NumericProperty(1.)
    manager = ObjectProperty()
    _anim = ObjectProperty(allownone=True)

    def start(self, manager):
        self.manager = manager
        self._anim = Animation(d=self.duration)
        self._anim.bind(on_progress=self._on_progress, on_complete=self._on_complete)

        self.add_screen(self.screen_in)
        self.screen_in.transition_value = 0.
        self.screen_in.transition_mode = 'in'
        self.screen_out.transition_value = 0.
        self.screen_out.transition_mode = 'out'

        self._anim.start(self)
        self.on_progress(0)

    def stop(self):
        if self._anim:
            self._anim.cancel(self)
            self.on_complete()
            self._anim = None

    def add_screen(self, screen):
        self.manager.real_add_widget(screen)

    def remove_screen(self, screen):
        self.manager.real_remove_widget(screen)

    def _on_progress(self, *l):
        alpha = l[-1]
        self.screen_in.transition_value = alpha
        self.screen_out.transition_value = 1. - alpha
        self.on_progress(alpha)

    def _on_complete(self, *l):
        self.on_complete()
        self._anim = None

    def on_complete(self):
        self.remove_screen(self.screen_out)

    def on_progress(self, progression):
        pass


class SlideTransition(Transition):
    direction = OptionProperty('left', options=('left', 'right', 'top', 'down'))

    def on_progress(self, progression):
        a = self.screen_in
        b = self.screen_out
        manager = self.manager
        direction = self.direction
        if direction == 'left':
            a.y = b.y = manager.y
            a.x = manager.x + manager.width * (1 - progression)
            b.x = manager.x - manager.width * progression
        elif direction == 'right':
            a.y = b.y = manager.y
            b.x = manager.x + manager.width * progression
            a.x = manager.x - manager.width * (1 - progression)
        elif direction == 'top':
            a.x = b.x = manager.x
            a.y = manager.y + manager.height * (1 - progression)
            b.y = manager.y - manager.height * progression
        elif direction == 'down':
            a.x = b.x = manager.x
            b.y = manager.y + manager.height * progression
            a.y = manager.y - manager.height * (1 - progression)

class SwapTransition(Transition):

    def on_progress(self, progression):
        a = self.screen_in
        b = self.screen_out
        manager = self.manager
        from math import cos, pi
        a.scale = 0.5 + progression * 0.5
        b.scale = 1. - progression * 0.9
        x = (cos(progression * 2 * pi - pi) + 1) / 2.
        a.x = manager.x + x * (manager.width / 2.)
        a.center_y = b.center_y = manager.center_y




class ScreenManagerBase(FloatLayout):
    current = StringProperty(None)
    transition = ObjectProperty(SlideTransition())

    _screens = ListProperty()
    _current_screen = ObjectProperty(None)

    def add_widget(self, screen):
        assert(isinstance(screen, Screen))
        if screen.name in [s.name for s in self._screens]:
            Logger.warning('ScreenManagerBase: duplicated screen name %r' %
                    screen.name)
        if screen.manager:
            raise Exception('ScreenManager: you are adding a screen already managed by somebody else')
        screen.manager = self
        self._screens.append(screen)
        if self.current is None:
            self.current = screen.name

    def real_add_widget(self, *l):
        super(ScreenManagerBase, self).add_widget(*l)

    def real_remove_widget(self, *l):
        super(ScreenManagerBase, self).remove_widget(*l)

    def on_current(self, instance, value):
        screen = self.get_screen(value)
        if not screen:
            return

        previous_screen = self._current_screen
        self._current_screen = screen
        if previous_screen:
            self.transition.stop()
            self.transition.screen_in = screen
            self.transition.screen_out = previous_screen
            self.transition.start(self)
        else:
            self.real_add_widget(screen)

    def get_screen(self, name):
        for screen in self._screens:
            if screen.name == name:
                return screen

class FullScreenManager(ScreenManagerBase):
    pass


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.lang import Builder
    Builder.load_string('''
<Screen>:
    canvas:
        Color:
            rgb: 1, 1, 1 if self.name == 'test1' else 0
        Rectangle:
            size: self.size

    Label:
        text: root.name
        font_size: 45
        color: (0, 0, 0, 1)
''')

    class TestApp(App):
        def change_view(self, *l):
            #d = ('left', 'top', 'down', 'right')
            #di = d.index(self.sm.transition.direction)
            #self.sm.transition.direction = d[(di + 1) % len(d)]
            self.sm.current = 'test2' if self.sm.current == 'test1' else 'test1'

        def build(self):
            root = FloatLayout()
            self.sm = sm = FullScreenManager(transition=SwapTransition())

            sm.add_widget(Screen(name='test1'))
            sm.add_widget(Screen(name='test2'))

            btn = Button(size_hint=(None, None))
            btn.bind(on_release=self.change_view)
            root.add_widget(sm)
            root.add_widget(btn)
            return root

    TestApp().run()



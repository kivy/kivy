
__all__ = ('AnimatedButton')

from kivy.factory import Factory
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.properties import StringProperty, OptionProperty, \
                            ObjectProperty, BooleanProperty


class AnimatedButton(Label):

    state = OptionProperty('normal', options=('normal', 'down'))
    allow_stretch = BooleanProperty(True)
    keep_ratio = BooleanProperty(False)
    border = ObjectProperty(None)
    anim_delay = ObjectProperty(None)
    background_normal = StringProperty(
        'atlas://data/images/defaulttheme/button')
    texture_background = ObjectProperty(None)
    background_down = StringProperty(
            'atlas://data/images/defaulttheme/button_pressed')

    def __init__(self, **kwargs):
        super(AnimatedButton, self).__init__(**kwargs)

        self.register_event_type('on_press')
        self.register_event_type('on_release')
        # borderImage.border by default is ...
        self.border = (16, 16, 16, 16)
        # Image to display depending on state
        self.img = Image(
            source=self.background_normal,
            allow_stretch=self.allow_stretch,
            keep_ratio=self.keep_ratio,
            mipmap=True)

        # reset animation if anim_delay is changed
        def anim_reset(*l):
            self.img.anim_delay = self.anim_delay

        self.bind(anim_delay=anim_reset)
        self.anim_delay = .1
        # update self.texture when image.texture changes
        self.img.bind(texture=self.on_tex_changed)
        self.on_tex_changed()

        # update image source when background image is changed
        def background_changed(*l):
            self.img.source = self.background_normal
            self.anim_delay = .1

        self.bind(background_normal=background_changed)

    def on_tex_changed(self, *largs):
        self.texture_background = self.img.texture

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if repr(self) in touch.ud:
            return False
        touch.grab(self)
        touch.ud[repr(self)] = True
        _animdelay = self.img.anim_delay
        self.img.source = self.background_down
        self.img.anim_delay = _animdelay
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        return repr(self) in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        assert(repr(self) in touch.ud)
        touch.ungrab(self)
        _animdelay = self.img._coreimage.anim_delay
        self.img.source = self.background_normal
        self.anim_delay = _animdelay
        self._do_release()
        self.dispatch('on_release')
        return True

    def on_press(self):
        pass

    def on_release(self):
        pass


Factory.register('AnimatedButton', cls=AnimatedButton)

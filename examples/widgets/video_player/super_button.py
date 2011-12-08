from kivy.app import App
from kivy.uix.image import Image
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, \
    BooleanProperty, DictProperty, ListProperty

class SuperButton(Image):
    app = ObjectProperty( None )
    background_normal = StringProperty( '' )
    background_down = StringProperty( '' )

    def __init__(self, **kwargs):
        super(SuperButton,self).__init__(**kwargs)
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        self.source = self.background_normal
        #self.image = Image(source = self.background_normal, size_hint =(1,1) )
        #self.image.bind(size = self.size)
        #self.add_widget(self.image)

    def get_scale(self, size):
        pass

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        #touch
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        #dispatch
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        return self in touch.ud

    def on_touch_up(self, touch):
        #touch
        if touch.grab_current is not self:
            return
        assert(self in touch.ud)
        touch.ungrab(self)
        #dispatch
        self._do_release()
        self.dispatch('on_release')
        
        return True

    def on_press(self):
        #background image
        if self.background_down !='' : 
            self.source = self.background_down

    def on_release(self):
        #background image
        if self.background_down !='' : 
            self.source = self.background_normal
        


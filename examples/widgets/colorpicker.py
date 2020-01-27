from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, StringProperty
from kivy.graphics import Color, Point, GraphicException

from math import sqrt
from os import walk
from os.path import dirname, join

from kivy.lang import Builder

Builder.load_string('''
#:import os os
<Picture>:
    # each time a picture is created, the image can delay the loading
    # as soon as the image is loaded, ensure that the center is changed
    # to the center of the screen.
    on_size: self.center = app.main_root_widget.center
    size: img.size
    size_hint: None, None
    on_touch_down: if self.collide_point(*args[1].pos): app.current_image = img

    Image:
        id: img
        source: root.source

        # create initial image to be 400 pixels width
        size: 400, 400 / self.image_ratio

        # add shadow background
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            BorderImage:
                source: '../demo/pictures/shadow32.png'
                border: (36, 36, 36, 36)
                size:(self.width + 72, self.height + 72)
                pos: (-36, -36)

<ColorSelector>:
    color: 1, 1, 1, 1
    title: 'Color Slector'
    content:content
    BoxLayout:
        id: content
        orientation: 'vertical'
        ColorPicker:
            id: clr_picker
            color: root.color
        BoxLayout:
            size_hint_y: None
            height: '27sp'
            Button:
                text: 'ok'
                on_release:
                    root.color = clr_picker.color
                    root.dismiss()
            Button:
                text: 'cancel'
                on_release: root.dismiss()

<LeftPanel@BoxLayout>
    orientation: 'vertical'
    padding: '2pt'
    canvas.before:
        Color:
            rgba: .5, .4, .9, .2
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        size_hint_y: None
        font_size: '18sp'
        text_size: self.width, None
        valign: 'middle'
        halign: 'center'
        height: self.texture.size[1] if self.texture else 10
        text:
            ("Selected Image:\\n" + app.current_image.source.split(os.sep)[-1]
            if app.current_image else 'None')
    Button:
        text: 'Brush'
        size_hint_y: None
        height: self.parent.width
        on_release:
            app.color_selector.open()
            app.color_mode = 'brush'
        Image:
            color: app.color_selector.color
            source: '../demo/touchtracer/particle.png'
            allow_stretch: True
            size: self.parent.size
            pos: self.parent.pos
    Button:
        text: 'cursor'
        on_release: app.color_mode = 'cursor'
    Button:
        text: 'clear'
        on_release:
            app.handle_clear()

<MainRootWidget>
    current_image: None
    client_area: client_area
    RelativeLayout:
        id: client_area
    Splitter:
        sizable_from: 'left'
        size_hint: None, 1
        width: '99dp'
        LeftPanel:

''')


def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
    if dist < steps:
        return
    o = []
    m = dist / steps
    for i in range(1, int(m)):
        mi = i / m
        lastx = x1 + dx * mi
        lasty = y1 + dy * mi
        o.extend([lastx, lasty])
    return o


class ColorSelector(Popup):
    pass


class Picture(Scatter):

    source = StringProperty(None)
    '''path to the Image to be loaded
    '''

    def __init__(self, **kwargs):
        super(Picture, self).__init__(**kwargs)
        self._app = App.get_running_app()

    def on_touch_down(self, touch):
        _app = self._app
        if (_app.color_mode[0] == 'c' or
                not self.collide_point(*touch.pos)):
            return super(Picture, self).on_touch_down(touch)
        ud = touch.ud
        ud['group'] = g = str(touch.uid)
        _pos = list(self.ids.img.to_widget(*touch.pos))
        _pos[0] += self.parent.x
        with self.ids.img.canvas.after:
            ud['color'] = Color(*_app.color_selector.color, group=g)
            ud['lines'] = Point(points=(_pos),
                            source='../demo/touchtracer/particle.png',
                            pointsize=5, group=g)
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        _app = self._app
        if _app.color_mode[0] == 'c' or not self.collide_point(*touch.pos):
            return super(Picture, self).on_touch_move(touch)
        ud = touch.ud
        _pos = list(self.ids.img.to_widget(*touch.pos))
        _pos[0] += self.parent.x
        points = ud['lines'].points
        oldx, oldy = points[-2], points[-1]
        points = calculate_points(oldx, oldy, _pos[0], _pos[1])
        if points:
            try:
                lp = ud['lines'].add_point
                for idx in range(0, len(points), 2):
                    lp(points[idx], points[idx + 1])
            except GraphicException:
                pass

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        _app = self._app
        if _app.color_mode[0] == 'c':
            return super(Picture, self).on_touch_up(touch)
        touch.ungrab(self)
        ud = touch.ud
        self.canvas.remove_group(ud['group'])


class MainRootWidget(BoxLayout):

    clent_area = ObjectProperty(None)
    # The Client Area in which all editing is Done

    def on_parent(self, instance, parent):
        if parent:
            _dir = join(dirname(__file__), '../demo/pictures/images/')
            for image in list(walk(_dir))[0][2]:
                if image.find('jpg') > -1:
                    self.client_area.add_widget(Picture(source=_dir + image))


class MainApp(App):

    main_root_widget = ObjectProperty(None)
    # we will be accessing this later as App.main_root_widget

    current_image = ObjectProperty(None)
    '''This is a handle to the currently selected image on which the effects
    would be applied.'''

    color_mode = StringProperty('cursor')
    '''This defines the current mode `brush` or `cursor`. `brush` mode allows
    adding brush strokes to the currently selected Image.
    '''

    def build(self):
        self.color_selector = ColorSelector()
        self.main_root_widget = MainRootWidget()
        return self.main_root_widget

    def handle_clear(self):
        if self.current_image:
            self.current_image.canvas.after.clear()


if __name__ == '__main__':
    MainApp().run()

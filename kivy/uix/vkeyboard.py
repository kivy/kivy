'''
VKeyboard: Virtual keyboard with custom layout support
'''
__all__ = ('VKeyboard', )

from kivy import kivy_data_dir
from kivy.config import Config
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, \
    BooleanProperty, DictProperty, OptionProperty, ListProperty
from kivy.logger import Logger
from kivy.graphics import Color, BorderImage, Canvas
from kivy.clock import Clock
from kivy.core.image import Image
from kivy.resources import resource_find

from os.path import join, splitext
from os import listdir
from json import loads


default_layout_path = join(kivy_data_dir, 'keyboards')

class VKeyboard(Scatter):
    '''
    VKeyboard is an onscreen keyboard with multitouch support.
    Its layout is entirely customizable and you can switch between available
    layouts using a button in the bottom right of the widget.

    List of internal actions available :

    * backspace
    * capslock
    * enter
    * escape
    * layout (to display layout list)
    * shift
    * shift_L
    * shift_R

    '''
    target = ObjectProperty(None)
    callback = ObjectProperty(None)
    layout = DictProperty({})
    layout_path = StringProperty(default_layout_path)
    available_layouts = DictProperty({})

    # internal variables
    mode = OptionProperty('normal', options=('normal', 'shift'))
    layout_geometry = DictProperty({})
    have_capslock = BooleanProperty(False)
    have_shift = BooleanProperty(False)
    active_keys = DictProperty({})
    font_size = NumericProperty(15)
    font_name = StringProperty('data/fonts/DejaVuSans.ttf')

    # styling
    margin_hint = ListProperty([.05, .06, .05, .06])
    key_margin = ListProperty([2, 2, 2, 2])
    background_color = ListProperty([1, 1, 1, 1])
    background = StringProperty('data/images/vkeyboard_background.png')
    key_background_color = ListProperty([1, 1, 1, 1])
    key_background_normal = StringProperty(
            'data/images/vkeyboard_key_normal.png')
    key_background_down = StringProperty('data/images/vkeyboard_key_down.png')
    background_border = ListProperty([16, 16, 16, 16])
    key_border = ListProperty([8, 8, 8, 8])

    def __init__(self, **kwargs):
        # XXX move to style.kv
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('scale_min', .4)
        kwargs.setdefault('scale_max', 1.6)
        kwargs.setdefault('size', (700, 200))
        super(VKeyboard, self).__init__(**kwargs)

        self.bind(have_shift=self._update_mode,
                have_capslock=self._update_mode)

        # force initial loading of layout path if not done
        if self.layout_path == default_layout_path:
            self.on_layout_path(self, self.layout_path)

        # ensure we have default layouts
        available_layouts = self.available_layouts
        if not available_layouts:
            Logger.critical('VKeyboard: unable to load defaults layouts')

        # load the default layout from configuration
        if self.layout == {}:
            layout_id = Config.get('widgets', 'keyboard_layout')
            if layout_id not in available_layouts:
                Logger.error(
                    'Vkeyboard: <%s> keyboard layout mentionned in '
                    'conf file was not found, fallback on qwerty' %
                    layout_id)
                layout_id = 'qwerty'
            self.layout = available_layouts[layout_id]

        # create a top layer to draw active keys on
        with self.canvas:
            self.background_key_layer = Canvas()
            self.active_keys_layer = Canvas()

        # prepare layout widget
        self.refresh_keys_hint()
        self.refresh_keys()
        self.draw_keys()

    def _update_mode(self, instance, value):
        # update mode according to capslock and shift key
        mode = self.have_capslock != self.have_shift
        mode = 'shift' if mode else 'normal'
        if mode != self.mode:
            self.mode = mode
            self.refresh(False)

    def on_layout_path(self, instance, value):
        # first load available layouts from json files
        # XXX fix to be able to reload layout when path is changing
        available_layouts = self.available_layouts
        for fname in listdir(value):
            basename, extension = splitext(fname)
            if extension != '.json':
                continue
            filename = join(value, fname)
            with open(filename, 'r') as fd:
                json_content = fd.read()
                layout = loads(json_content)
            available_layouts[basename] = layout

    def change_layout(self):
        # XXX implement popup with all available layouts
        assert(0)

    def refresh(self, force=False):
        # recreate the whole widgets and graphics according to selected layout
        self.clear_widgets()
        if force:
            self.reset_special_keys()
            self.refresh_keys_hint()
        self.refresh_keys()
        self.draw_keys()
        self.refresh_active_keys_layer()

    def refresh_active_keys_layer(self):
        self.active_keys_layer.clear()
        self.draw_active_keys()

    def refresh_keys_hint(self):
        layout = self.layout
        layout_cols = layout['cols']
        layout_rows = layout['rows']
        layout_geometry = self.layout_geometry
        mtop, mright, mbottom, mleft = self.margin_hint

        # get relative EFFICIENT surface of the layout without external margins
        el_hint = 1. - mleft - mright
        eh_hint = 1. - mtop - mbottom
        ex_hint = 0 + mleft
        ey_hint = 0 + mbottom

        # get relative unit surface
        uw_hint = (1. / layout_cols) * el_hint
        uh_hint = (1. / layout_rows) * eh_hint
        layout_geometry['U_HINT'] = (uw_hint, uh_hint)

        # calculate individual key RELATIVE surface and pos (without key margin)
        current_y_hint = ey_hint + eh_hint
        for line_nb in xrange(1, layout_rows + 1):
            current_y_hint -= uh_hint
            # get line_name
            line_name = '%s_%d' % (self.mode, line_nb)
            line_hint = 'LINE_HINT_%d' % line_nb
            layout_geometry[line_hint] = []
            current_x_hint = ex_hint
            # go through the list of keys (tuples of 4)
            for key in layout[line_name]:
                # calculate relative pos, size
                layout_geometry[line_hint].append([
                    (current_x_hint, current_y_hint),
                    (key[3] * uw_hint, uh_hint)])
                current_x_hint += key[3] * uw_hint

        self.layout_geometry = layout_geometry

    def refresh_keys(self):
        layout = self.layout
        layout_rows = layout['rows']
        layout_geometry = self.layout_geometry
        w, h = self.size
        kmtop, kmright, kmbottom, kmleft = self.key_margin
        uw_hint, uh_hint = layout_geometry['U_HINT']

        for line_nb in xrange(1, layout_rows + 1):
            llg = layout_geometry['LINE_%d' % line_nb] = []
            llg_append = llg.append
            for key in layout_geometry['LINE_HINT_%d' % line_nb]:
                x_hint, y_hint = key[0]
                w_hint, h_hint = key[1]
                kx = x_hint * w
                ky = y_hint * h
                kw = w_hint * w
                kh = h_hint * h

                # now adjust, considering the key margin
                kx = int(kx + kmleft)
                ky = int(ky + kmbottom)
                kw = int(kw - kmleft - kmright)
                kh = int(kh - kmbottom - kmtop)

                pos = (kx, ky)
                size = (kw, kh)
                llg_append((pos, size))

        self.layout_geometry = layout_geometry

    def draw_keys(self):
        layout = self.layout
        layout_rows = layout['rows']
        layout_geometry = self.layout_geometry
        mode = self.mode

        # draw background
        w, h = self.size

        background = resource_find(self.background)
        texture = Image(background, mipmap=True).texture
        with self.background_key_layer:
            Color(*self.background_color)
            BorderImage(texture=texture, size=self.size,
                    border=self.background_border)

        # XXX seperate drawing the keys and the fonts to avoid
        # XXX reloading the texture each time

        # first draw keys without the font
        key_normal = resource_find(self.key_background_normal)
        texture = Image(key_normal, mipmap=True).texture
        for line_nb in xrange(1, layout_rows + 1):
            for pos, size in layout_geometry['LINE_%d' % line_nb]:
                with self.background_key_layer:
                    Color(self.key_background_color)
                    BorderImage(texture=texture, pos=pos, size=size,
                            border=self.key_border)

        # then draw the text
        # calculate font_size
        font_size = int(w) / 46
        # draw
        for line_nb in xrange(1, layout_rows + 1):
            key_nb = 0
            for pos, size in layout_geometry['LINE_%d' % line_nb]:
                # retrieve the relative text
                text = layout[mode +'_'+ str(line_nb)][key_nb][0]
                # print text
                l = Label(text=text, font_size=font_size, pos=pos, size=size,
                        font_name=self.font_name)
                self.add_widget(l)
                key_nb += 1

    def draw_active_keys(self):
        active_keys = self.active_keys
        layout_geometry = self.layout_geometry
        self.background_border = (16, 16, 16, 16)
        background = resource_find(self.key_background_down)
        texture = Image(background, mipmap=True).texture

        with self.active_keys_layer:
            Color(1, 1, 1)
            for line_nb, index in active_keys.itervalues():
                pos, size = layout_geometry['LINE_%d' % line_nb][index]
                BorderImage(texture=texture, pos=pos, size=size,
                        border=self.key_border)

    def send(self, key_data):
        character, b, c, d = key_data
        # print character
        target = self.target
        return

        if key_data[2] is None:
            target.insert_text(key_data[1])
        else:
            target._key_down(key_data, repeat=False)

    def get_key_at_pos(self, x, y):
        w, h = self.size
        x_hint = x / w
        # focus on the surface without margins
        layout_geometry = self.layout_geometry
        layout = self.layout
        layout_rows = layout['rows']
        mtop, mright, mbottom, mleft = self.margin_hint

        # get the line of the layout
        e_height = h - (mbottom + mtop) * h # efficient height in pixels
        line_height = e_height / layout_rows # line height in px
        y = y - mbottom * h
        line_nb = layout_rows - int(y / line_height)

        if line_nb > layout_rows:
            line_nb = layout_rows
        if line_nb < 1:
            line_nb = 1

        # get the key within the line
        key_index = ''
        current_key_index =0
        for key in layout_geometry['LINE_HINT_%d' % line_nb]:
            if x_hint >= key[0][0] and x_hint < key[0][0] + key[1][0]:
                key_index = current_key_index
                break
            else:
                current_key_index +=1
        if key_index == '':
            return None

        # get the full character
        key = self.layout['%s_%d' % (self.mode, line_nb)][key_index]

        return [key, (line_nb, key_index)]

    def touch_is_in_margin(self, x, y):
        w, h = self.size
        mtop, mright, mbottom, mleft = self.margin_hint

        x_hint = x / w
        y_hint = y/h

        if x_hint > mleft and x_hint < 1. - mright \
            and y_hint > mbottom and y_hint < 1. - mtop:
            return False
        else:
            return True

    def get_local_pos(self, pos):
        # return self.to_local(pos[0], pos[1])
        x, y = pos
        x_widget = self.x
        y_widget = self.y
        return (x - x_widget, y - y_widget)

    def process_key_on(self, touch):
        x, y = self.to_local(*touch.pos)
        key = self.get_key_at_pos(x, y)
        if not key:
            return

        key_data = key[0]
        displayed_char, internal, special_char, size = key_data
        line_nb, key_index = key[1]

        # save pressed key on the touch
        ud = touch.ud[self.uid] = {}
        ud['key'] = key

        # send info to the bus
        if not special_char in ('shift_L', 'shift_R', 'capslock', 'layout'):
            self.send(key_data)

        uid = touch.uid

        # for caps lock or shift only:
        if special_char is not None:
            if special_char == 'capslock':
                self.have_capslock = not self.have_capslock
                uid = -1
            elif special_char in ('shift_L', 'shift_R'):
                self.have_shift = True
            elif special_char == 'layout':
                self.change_layout()

        # save key as an active key for drawing
        self.active_keys[uid] = key[1]
        self.refresh_active_keys_layer()

    def process_key_up(self, touch):
        uid = touch.uid

        # save pressed key on the touch
        key_data, key = touch.ud[self.uid]['key']
        displayed_char, internal, special_char, size = key_data

        if special_char == 'capslock':
            uid = -1

        if uid in self.active_keys:
            self.active_keys.pop(uid, None)
            if special_char in ('shift_L', 'shift_R'):
                self.have_shift = False
            if special_char == 'capslock' and self.have_capslock:
                self.active_keys[-1] = key
            self.refresh_active_keys_layer()

    def on_touch_down(self, touch):
        x, y = touch.pos
        if not self.collide_point(x, y):
            return

        x, y = self.to_local(x, y)
        if not self.touch_is_in_margin(x, y):
            self.process_key_on(touch)
            touch.grab(self)
        else:
            super(VKeyboard, self).on_touch_down(touch)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.process_key_up(touch)
        return super(VKeyboard, self).on_touch_up(touch)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(VKeyboard())

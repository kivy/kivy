'''
Show a circle under all touchs
'''

import os
from kivy import MTWidget, set_color, getCurrentTouches, kivy_data_dir, Image

if not 'KIVY_DOC' in os.environ:
    ring_fn = os.path.join(kivy_data_dir, 'ring.png')
    ring_img = Image(ring_fn)
    ring_img.scale = .30
    ring_img.anchor_x = ring_img.width / 2
    ring_img.anchor_y = ring_img.height / 2

class TouchRing(MTWidget):
    def __init__(self, **kwargs):
        super(TouchRing, self).__init__(**kwargs)

    def on_update(self):
        self.bring_to_front()

    def draw(self):
        color = self.style.get('color')
        ring_img.color = color
        for touch in getCurrentTouches():
            alpha = color[3]
            if 'kinetic' in touch.profile:
                alpha = .2

            # draw touch
            ring_img.opacity = alpha
            ring_img.pos = touch.pos
            ring_img.draw()

def start(win, ctx):
    ctx.w = TouchRing()
    win.add_widget(ctx.w)

def stop(win, ctx):
    win.remove_widget(ctx.w)

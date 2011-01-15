'''
Get all informations of a touch
'''

from kivy import MTWidget, MTSpeechBubble, getCurrentTouches


class TouchInfos(MTWidget):

    def __init__(self, **kwargs):
        super(TouchInfos, self).__init__(**kwargs)
        self.bubbles = {}

    def text_info(self, touch):
        infos = []
        infos.append('ID: %s' % (str(touch.id)))
        infos.append('UID: %s' % (str(touch.uid)))
        infos.append('Class: %s' % str(touch.__class__.__name__))
        infos.append('Raw pos: (%.3f, %.3f)' % (touch.sx, touch.sy))
        infos.append('Scr Pos: (%d, %d)' % (touch.xpos, touch.ypos))
        if hasattr(touch, 'xmot'):
            infos.append('Mot: (%.2f, %.2f)' % (touch.xmot, touch.ymot))
        infos.append('Double Tap: %s' % (touch.is_double_tap))
        infos.append('Device: %s' % (touch.device))
        return "\n".join(infos)

    def on_update(self):
        self.bring_to_front()

    def draw(self):
        bubbles = self.bubbles
        get = self.bubbles.get
        info = self.text_info
        current = getCurrentTouches()
        for touch in current:
            uid = touch.uid
            bubble = get(uid, None)
            if not bubble:
                bubble = MTSpeechBubble(
                    size=(150, 100), color=(0, 0, 0, 1), font_size=9)
                self.bubbles[uid] = bubble
            bubble.pos = touch.pos
            bubble.label = info(touch)
            bubble.dispatch('on_draw')

        alive = [x.uid for x in current]
        for uid in bubbles.keys()[:]:
            if uid not in alive:
                del bubbles[uid]


def start(win, ctx):
    ctx.w = TouchInfos()
    win.add_widget(ctx.w)


def stop(win, ctx):
    win.remove_widget(ctx.w)

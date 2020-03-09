from kivy.properties import BooleanProperty, ListProperty


class HoverBehavior(object):

    hovered = BooleanProperty(False)
    hover_ids = ListProperty()

    __events__ = ('on_hover_start', 'on_hover_move', 'on_hover_end')

    def __init__(self, **kwargs):
        self.add_motion_event('hover')
        super().__init__(**kwargs)

    def on_motion(self, etype, me):
        if super().on_motion(etype, me):
            return True
        if me.type_name != 'hover':
            return False
        if etype == 'end':
            if me.device_id in self.hover_ids:
                self.hover_ids.remove(me.device_id)
                self.hovered = bool(self.hover_ids)
                self.dispatch('on_hover_end', me)
            return
        if self.collide_point(*me.pos):
            if me.device_id in self.hover_ids:
                self.dispatch('on_hover_move', me)
            else:
                self.hover_ids.append(me.device_id)
                self.hovered = True
                self.dispatch('on_hover_start', me)
            me.grab(self)
            return True

    def on_hover_start(self, me):
        pass

    def on_hover_move(self, me):
        pass

    def on_hover_end(self, me):
        pass

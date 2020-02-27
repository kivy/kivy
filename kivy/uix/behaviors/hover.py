from kivy.properties import BooleanProperty


class HoverBehavior(object):
    '''TODO: Multi-hover support
    '''

    hovered = BooleanProperty(False)

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
            if self.hovered:
                self.hovered = False
                self.dispatch('on_hover_end', me)
            return
        if self.collide_point(*me.pos):
            if self.hovered:
                self.dispatch('on_hover_move', me)
            else:
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

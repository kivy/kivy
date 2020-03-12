from kivy.properties import BooleanProperty, ListProperty, OptionProperty


class HoverBehavior(object):

    hovered = BooleanProperty(False)
    hover_ids = ListProperty()
    hover_mode = OptionProperty('default', options=['default', 'self', 'all'])

    __events__ = ('on_hover_start', 'on_hover_move', 'on_hover_end')

    def __init__(self, **kwargs):
        self.add_motion_event('hover')
        super().__init__(**kwargs)

    def on_motion(self, etype, me):
        if me.type_name != 'hover':
            return super().on_motion(etype, me)
        if me.grab_current is self:
            if self.handle_hover_event_on_self(etype, me):
                return True
            return super().on_motion(etype, me)
        if self.hover_mode == 'default':
            if super().on_motion(etype, me):
                return True
            return self.handle_hover_event_on_self(etype, me)
        if self.hover_mode == 'self':
            return self.handle_hover_event_on_self(etype, me)
        if self.hover_mode == 'all':
            return any(
                (super().on_motion(etype, me),
                 self.handle_hover_event_on_self(etype, me))
            )

    def on_hover_ids(self, widget, hover_ids):
        self.hovered = bool(hover_ids)

    def handle_hover_event_on_self(self, etype, me):
        if me.grab_current is self:
            if etype == 'end' and me.device_id in self.hover_ids:
                self.hover_ids.remove(me.device_id)
                self.dispatch('on_hover_end', me)
            return True
        if self.collide_point(*me.pos):
            if etype == 'end':
                if me.device_id in self.hover_ids:
                    self.hover_ids.remove(me.device_id)
                    self.dispatch('on_hover_end', me)
                return True
            if me.device_id in self.hover_ids:
                self.dispatch('on_hover_move', me)
            else:
                self.hover_ids.append(me.device_id)
                self.dispatch('on_hover_start', me)
            me.grab(self)
            return True

    def on_hover_start(self, me):
        pass

    def on_hover_move(self, me):
        pass

    def on_hover_end(self, me):
        pass

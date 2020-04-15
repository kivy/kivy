from kivy.properties import BooleanProperty, ListProperty, OptionProperty


class HoverBehavior(object):

    hovered = BooleanProperty(False)
    hover_ids = ListProperty()
    hover_mode = OptionProperty('default', options=['default', 'self', 'all'])

    __events__ = ('on_hover_start', 'on_hover_update', 'on_hover_end')

    def __init__(self, **kwargs):
        self.add_motion_event('hover')
        super().__init__(**kwargs)

    def on_motion(self, etype, me):
        if me.type_name != 'hover':
            return super().on_motion(etype, me)
        if me.device_id not in self.hover_ids:
            return self.dispatch('on_hover_start', me)
        if etype == 'update':
            return self.dispatch('on_hover_update', me)
        if etype == 'end':
            return self.dispatch('on_hover_end', me)

    def handle_hover_event(self, etype, me):
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

    def handle_hover_event_on_self(self, etype, me):
        if me.grab_current is self:
            if etype == 'end' and me.device_id in self.hover_ids:
                self.hover_ids.remove(me.device_id)
            return True
        if self.disabled and self.collide_point(*me.pos):
            return True
        if self.collide_point(*me.pos):
            if etype == 'end':
                if me.device_id in self.hover_ids:
                    self.hover_ids.remove(me.device_id)
                return True
            if me.device_id not in self.hover_ids:
                self.hover_ids.append(me.device_id)
            me.grab(self)
            return True

    def on_hover_ids(self, widget, hover_ids):
        self.hovered = bool(hover_ids)

    def on_hover_start(self, me):
        return self.handle_hover_event(me.ud['me.etype'], me)

    def on_hover_update(self, me):
        return self.handle_hover_event(me.ud['me.etype'], me)

    def on_hover_end(self, me):
        return self.handle_hover_event(me.ud['me.etype'], me)


class StencilViewHoverMixin(object):

    def on_motion(self, etype, me):
        if me.type_name != 'hover':
            return super().on_motion(etype, me)
        if me.grab_current is self or self.collide_point(*me.pos):
            return super().on_motion(etype, me)

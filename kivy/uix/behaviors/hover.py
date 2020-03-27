from kivy.properties import (
    BooleanProperty,
    ListProperty,
    OptionProperty,
    DictProperty
)


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


class StencilViewHoverMixin(object):

    def on_motion(self, etype, me):
        if me.type_name != 'hover':
            return super().on_motion(etype, me)
        if me.grab_current is self or self.collide_point(*me.pos):
            return super().on_motion(etype, me)


class RecycleLayoutHoverMixin(object):

    last_hover = DictProperty()

    def on_motion(self, etype, me):
        handled = super().on_motion(etype, me)
        if handled and me.type_name == 'hover':
            self.last_hover[me.device_id] = me
        return handled

    def remove_widget(self, widget):
        last_hover = self.last_hover
        if last_hover:
            hovered_widgets = []
            for w in widget.walk(restrict=True):
                if isinstance(w, HoverBehavior) and w.hovered:
                    hovered_widgets.append((w, w.hover_ids[:]))
            for w, hover_ids in hovered_widgets:
                for device_id in hover_ids:
                    me = last_hover[device_id]
                    me.grab_state = True
                    me.push()
                    me.apply_transform_2d(w.parent.to_widget)
                    me.grab_current = w
                    w.dispatch('on_motion', 'end', me)
                    me.grab_current = None
                    me.pop()
                    me.grab_state = False
        super().remove_widget(widget)

    def on_children(self, layout, children):
        if hasattr(super(), 'on_children'):
            super().on_children(layout, children)
        if not children:
            self.last_hover.clear()

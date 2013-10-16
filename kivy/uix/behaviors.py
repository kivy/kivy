'''
Behaviors
=========

.. versionadded:: 1.8.0

This module implements behaviors that can be mixed with existing base widgets.
For example, if you want to add a "button" capability to an `Image`, you could
do::


    class IconButton(ButtonBehavior, Image):
        pass

.. note::

    The behavior class must always be _before_ the widget class. If you don't
    specify the inheritance in this order, the behavior will not work.

'''

__all__ = ('ButtonBehavior', 'ToggleButtonBehavior')

from kivy.clock import Clock
from kivy.properties import OptionProperty, ObjectProperty
from weakref import ref


class ButtonBehavior(object):
    '''Button behavior.

    :Events:
        `on_press`
            Fired when the button is pressed.
        `on_release`: touch
            Fired when the button is released (i.e., the touch/click that
            pressed the button goes away). The first argument, touch, is the
            touch that caused the release.
    '''

    state = OptionProperty('normal', options=('normal', 'down'))
    '''State of the button, must be one of 'normal' or 'down'.
    The state is 'down' only when the button is currently touched/clicked,
    otherwise 'normal'.

    :data:`state` is an :class:`~kivy.properties.OptionProperty`.
    '''

    last_touch = ObjectProperty(None)
    '''Contains the last relevant touch received by the Button. This can be used
    in `on_press` or `on_release` in order to know which touch dispatched the
    event.

    .. versionadded:: 1.8.0

    :data:`last_touch` is a :class:`~kivy.properties.ObjectProperty`,
    default to None.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        super(ButtonBehavior, self).__init__(**kwargs)

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if super(ButtonBehavior, self).on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        self.last_touch = touch
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True
        if super(ButtonBehavior, self).on_touch_move(touch):
            return True
        return self in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(ButtonBehavior, self).on_touch_up(touch)
        assert(self in touch.ud)
        touch.ungrab(self)
        self.last_touch = touch
        self._do_release()
        self.dispatch('on_release', touch)
        return True

    def on_press(self):
        pass

    def on_release(self, *largs):
        pass

    def trigger_action(self, duration=0.1):
        '''Trigger whatever action(s) have been bound to the button by calling
        both the on_press and on_release callbacks.

        This simulates a quick button press without using any touch events.

        Duration is the length of the press in seconds. Pass 0 if you want
        the action to happen instantly.

        .. versionadded:: 1.8.0
        '''
        self._do_press()
        self.dispatch('on_press')

        def trigger_release(dt):
            self._do_release()
            self.dispatch('on_release', None)
        if not duration:
            trigger_release(0)
        else:
            Clock.schedule_once(trigger_release, duration)


class ToggleButtonBehavior(ButtonBehavior):
    '''ToggleButton behavior, see ToggleButton module documentation for more
    information.

    .. versionadded:: 1.8.0
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the button. If None, no group will be used (button is
    independent). If specified, :data:`group` must be a hashable object, like
    a string. Only one button in a group can be in 'down' state.

    :data:`group` is a :class:`~kivy.properties.ObjectProperty`
    '''

    def __init__(self, **kwargs):
        self._previous_group = None
        super(ToggleButtonBehavior, self).__init__(**kwargs)

    def on_group(self, *largs):
        groups = ToggleButtonBehavior.__groups
        if self._previous_group:
            group = groups[self._previous_group]
            for item in group[:]:
                if item() is self:
                    group.remove(item)
                    break
        group = self._previous_group = self.group
        if group not in groups:
            groups[group] = []
        r = ref(self, ToggleButtonBehavior._clear_groups)
        groups[group].append(r)

    def _release_group(self, current):
        if self.group is None:
            return
        group = self.__groups[self.group]
        for item in group[:]:
            widget = item()
            if widget is None:
                group.remove(item)
            if widget is current:
                continue
            widget.state = 'normal'

    def _do_press(self):
        self._release_group(self)
        self.state = 'normal' if self.state == 'down' else 'down'

    def _do_release(self):
        pass

    @staticmethod
    def _clear_groups(wk):
        # auto flush the element when the weak reference have been deleted
        groups = ToggleButtonBehavior.__groups
        for group in list(groups.values()):
            if wk in group:
                group.remove(wk)
                break

    @staticmethod
    def get_widgets(groupname):
        '''Return the widgets contained in a specific group. If the group
        doesn't exist, an empty list will be returned.

        .. important::

            Always release the result of this method! In doubt, do::

                l = ToggleButtonBehavior.get_widgets('mygroup')
                # do your job
                del l

        .. warning::

            It's possible that some widgets that you have previously deleted are
            still in the list. Garbage collector might need more elements before
            flushing it. The return of this method is informative, you've been
            warned!
        '''
        groups = ToggleButtonBehavior.__groups
        if groupname not in groups:
            return []
        return [x() for x in groups[groupname] if x()][:]


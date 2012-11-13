'''
GestureBox
==========

.. versionadded:: 1.5.0

The :class:`GestureBox` widget allows you to define gestures in a subclass and
bind to events on the named gestures. Any widgets added to the GestureBox are
rendered as normal in a BoxLayout. You can interact with them normally and the
touch events will be passed through. However, if you start to draw a gesture,
the GestureBox will capture the inputs and determine if they match any gestures
associated with the GestureBox. If they are, the events will not be propogated
and a on_gesture event will be fired instead.

Example::

    class ExampleApp(App):
        def build(self):
            gesture_box = GestureBox()
            gesture_box.add_gesture("down_swipe",
                'eNq1l91yIkcMhe/nReybpVr/0guwt6nyA6Qcm7Kp3dgUsNns20ejxsyQOGFTruFm4ND9taTTqJvb7ZftHz9WT5vD8dt+M3w+PXdtuH3cwXB383L/++Zm2GG+zQcNh7ubw3H/+mVzyI883H7dyXD7LuSuhg07HVGW83ev25fjOM3HafEv034ZRw076BGMIfzIKYDDuq0EHULBUEJDnMdo/hy/pWH9qa0aIXkDbOZuKk1lOPx2/9/LcC0jw1NfgZ1aCyEEFGaxTPjpjc4t8aq5slm+w+vwSh3sDGcy0DFCz9iwyRyO2IgacUQosf9E6F70ONOhEVh4a4oZIemH6Fj1R3ijE5GGgXCAIIbax+hYdFqIXqaiLEQvV/HsKkZjE5AWLiHK/DF6uYpnV0ExvTQT40am7jP6/9/uVK4SLEQvV4kWoperJAvRy1U6uwpg4gYkmGTlbEQTHZ2lOZulv57LX+8EVK5SLEPncpXPrjZ2x9xsetqa8/2OKKKR1cnCZS9jvU4vV5kWoperfHK1vCP1cPNsxRJp8gwPrOEUEM119Nav48tWtqXw5SvHhO87DjxEoHE6PsM30wAYq5cngPzEppQyVmApfDkrdMaDAUKeUtnEWrbM+QmSpyJLkAJgUFZKrhdHylqRpfBlrdhS+LJWJmsvWrmet/1IT1MMWSU8f89ofBWuZaxOxhIxWqAGs2KeFDrR00vM9bBhU5UceJ1eviotRC9bVRail6tqC9HLVJ1MJTU1b5EAJnKQiU6ei1mwEXgafh1uZapNpvK4J7IjJirQY0Kzg0aY5WbNy1q73iWtHDVaAl122mRnnj6QzLz/knPj4Amed9YIlHyaMFC/zoz/CB72m83L+X5vOl7wzYbbdV6kV21Yq1I+jjvz4X4mYheji61E8RK9XYjSRSgRoovQReyilciti9RFLRFPIs/F1kPKJCYxr29d1LnIPU63WfB5PnfxlBGVKLSK+YvHEaf0isUV+3EXPT2q9OjEip4eYYnSQ4meHlV61E4je3oV2Dq96mJPT3Dsd9NLcwTypUbj8J64FBjfwD3xcmYN5u9M61WoQq1BuzHhF2I3JmIu5joXpbEcAa39bUgrFS5U+WcQ0PBiCL3HpuuUrFjfwc+b7dPzcfwrmf/K1nmXz0kpf98+Hp9LzSqyd/H4+nWzv3952NQXVve5UT/9vn7d7V8fvz10mGdpV5a70iw/RPaqaiSrvwDFYvqM'
                )
            gesture_box.add_gesture("circle",
                'eNq1WNtyGzcMfd8fiV+iIS4EyB9QXzuTD+g4icbxpLU1ttI2f18QoHa5jpy12qlGAyUw9hA4ByQh3dx/vf/z++7u8Hz69nSYfumfxzTdfD7C9OHdw+0fh3fTEe2f9kHT84d3z6enx6+HZ/svTze/H/N0cxHkg4dNR2lQas8fH+8fTu2x0h6rrzz2a4uajhAZtBS+2yOA0z7tCDMkqjk1y0W1pfN3+zNN+/dpl0pGqmdLJcv0/PH25+uwr5Onu74EMxErVLeGMT3fNXQDT4C1kopbLVBhG92LB91Gh6RJinRb5A2ZF8euM/aP5JyxhVVShbBiJW9ho7OPcMZG1YTzWzTP2LgAm8XyBmx0bJqxsfSkm8UqMzaRluVduW5ju5o4qwkKmFWruM28cGLNcW3eriXOWi5kv8zbNK7GcwmbabtP0LXEWcuB7MY3pSVxVuRMiGFJaBOcXEzqYrZtwglLEsluBdOSen7R5LiN7nISzehAwsQZwC3yfwJ3PSnP4FZ31fnNrZX/PS8uKOkCvpBiFkfSF2Sz3PpoC9wVpTqDExXKmkvYmoc274S8nRZ2RXlR1B5u5xGG1bKcK7a5rtz77ILyIihVSVzL2bb8zuB4LefsgnJ+AzjQtTuUXVBeBCVRTKSMbq1HA/u9b7DMohpWSLbPFnZFuf4/6NklzYOki57N1rzAQ8YV/HY3Ztc0L5piXR0BMqAj1GItLmELb/OeXdQ87FKB8QhIOKDXOXGzOb2BGVc1D9sUaNxJNiPM6LQkbpbS9lbKrmpeVAXluRtTTloXdDs2B95z3UYXV1UWVe2aPydutqAO6HIt7+KqCm0f7A2+Fk1JkNyiTQ+b8C6rzJdpyrkoQUlhUx6IZ61XEi8uqyzXKSODTSphAcsAjnBlz4irKvN9CjVxsXEwu2UZ9iopXcmLuqgKWwOMb2JJNoh2y284B9Q11WU6En2NFuRrFVVXVJdhN71QdDhjBIe3a/3xtg3/n54Oh4d5lFdps7zNmjd7Rt2laY9ad3V88XQ6apluW0TxiAL2Yc7qTkqjs6RwSjgxnOBOhpUTw6krJ7kz06up2D3iETUiNB7L7pT+WLZhf3hJi5CIiLyU4zENZ5SlPYWoVSNZTeGMWv25vWnqzhq1amBKYNaotcTjuUdGrSXy8+rMGbWW7E6u66SpRUStJRbgvGZDW0QUXqICjgqqjE6q4dSVM19Yrawi4MJqwUIJyTBqg5TGOpC6F1be9ON6ttdGVkB+XNA2ZYREjwFfCgmSNJKC8/JBjMbyAN0bzLjS5k3dG9RoLJJK95axY9K52KBAohGShBeCAgncdIFcABj79nJI8JHzT0L6/kg/CQk+mFd5Q/BBtKoRZNzXZz4g+MC0YhSCD+hqXWhGgCAn1dcFxWAqdV0uND1gMJWCTIyeBnRy7CtZeLl7KbxRLPaykMObXu1k+1rpIb2VL20Hm9siJFKlTiTqylu7t4SXx31o35ZW3p4zpZVXLyxNsAq5xBIFH/1syH1FCj76Hs69PSn4KHU8k2w+D5aCZ+lbhKLqGvVJF5+i6hp0yRk3WiLFWSedfepdQOMBCtyFl/GsBe5a9xO4r8axESCNh7UNo+GFVw95YB57VHuaHL0Pebwy7DYPb79IevLcex/W3n7/0dobhWI+X1buzVEoytprhcYN/OVwf/fl1H70sql+ry83CbbfxP66/3z64iF2m9sJZxjmPT3+fni6ffh08L9w/IixfkGL68PDb8enx8/fPsVSedrnnc05diDYoIA2CpbUvu7t/gFuoPx3'
                )

            gesture_box.bind(on_gesture=self.gesture)
            button = Button(text="Click here and it gets propogated.\n"
                "Down stroke or draw a circle to invoke a gesture event")

            button.bind(on_press=self.button_press)
            gesture_box.add_widget(button)

            return gesture_box

        def gesture(self, gesture_box, gesture_name):
            print "{0} gesture occured".format(gesture_name)

        def button_press(self, button):
            print "The button got pressed"

    ExampleApp().run()

The easiest way to generate the long strings passed into add_gesture is to run
`python examples/gestures/gesture_board.py` Draw your chosen gesture in the
window and copy the long string from the gesture representation that shows up
in the terminal.
'''

__all__ = ('GestureBox',)

from math import sqrt
from functools import partial

from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Line
from kivy.clock import Clock
from kivy.gesture import Gesture, GestureDatabase
from kivy.properties import ObjectProperty, NumericProperty


class GestureBox(BoxLayout):
    'GestureBox class. See module documentation for more information.'

    gesture_timeout = NumericProperty(200)
    '''Timeout allowed to trigger the :data:`gesture_distance`, in milliseconds.
    If the user has not moved :data:`gesture_distance` within the timeout,
    the gesture will be disabled, and the touch event will go to the children.

    :data:`gesture_timeout` is a :class:`~kivy.properties.NumericProperty`,
    default to 200 (milliseconds)
    '''

    gesture_distance = NumericProperty('20dp')
    '''Distance to move before attempting to interpret as a gesture,
    in pixels. As soon as the distance has been traveled,
    the :class:`GestureBox` will interpret as a gesture.

    It is advisable that you base this value on the dpi of your target device's
    screen.

    :data:`gesture_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 20dp.
    '''
    # INTERNAL USE ONLY
    # used internally to store a touch and
    # dispatch it if the touch does not turn into a gesture
    _touch = ObjectProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        super(GestureBox, self).__init__(*args, **kwargs)
        self.gestures = GestureDatabase()
        self.register_event_type('on_gesture')

    def add_gesture(self, name, gesture_str):
        '''Add a recognized gesture to the database.

        :param name: a short identifier for the gesture. This value is passed
            to the on_gesture event to identify which gesture occurred.
        :param gesture_str: A (probably very long) string describing the
            gesture and suitable as input to the
            :meth:`GestureDatabase.str_to_gesture` method. The
            `examples/gestures/gesture_board.py` example is a good way to
            generate such gestures.'''
        gesture = self.gestures.str_to_gesture(gesture_str)
        gesture.name = name
        self.gestures.add_gesture(gesture)

    def on_touch_down(self, touch):
        '''(internal) When the touch down event occurs, we save it until we
        know for sure that a gesture is not being initiated. If a gesture
        is initiated we intercept all the touch and motion events. Otherwise,
        we release it to any child widgets.'''
        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('cavoid')] = True
            return
        if self._touch:
            return super(GestureBox, self).on_touch_down(touch)
        self._touch = touch
        uid = self._get_uid()
        touch.grab(self)
        touch.ud[uid] = {
            'mode': 'unknown',
            'time': touch.time_start}
        # This will be unscheduled if we determine that a gesture is being
        # attempted before it is called.
        Clock.schedule_once(self._change_touch_mode,
                self.gesture_timeout / 1000.)
        # Start storing the gesture line in case this turns into a gesture
        touch.ud['gesture_line'] = Line(points=(touch.x, touch.y))
        return True

    def on_touch_move(self, touch):
        '''(internal) As with touch down events, motion events are recorded
        until we know that a gesture is or is not being attempted.'''
        if self._get_uid('cavoid') in touch.ud:
            return
        if self._touch is not touch:
            super(GestureBox, self).on_touch_move(touch)
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True
        ud = touch.ud[self._get_uid()]
        if ud['mode'] == 'unknown':
            dx = abs(touch.ox - touch.x)
            dy = abs(touch.oy - touch.y)
            distance = sqrt(dx * dx + dy * dy)

            # If we've moved more than the thershold distance inside the
            # threshold time, treat as a gesture
            if distance > self.gesture_distance:
                Clock.unschedule(self._change_touch_mode)
                ud['mode'] = 'gesture'

        # Regardless of whether this is a known gesture or not, collect
        # the motion point in case it becomes one.
        try:
            touch.ud['gesture_line'].points += [touch.x, touch.y]
        except KeyError:
            pass

        return True

    def on_touch_up(self, touch):
        '''(internal) When the touch up occurs, we have to decide if a gesture
        was attempted. If so, we fire the on_gesture event. In all other cases
        we propogate the change to child widget.'''
        if self._get_uid('cavoid') in touch.ud:
            return
        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            ud = touch.ud[self._get_uid()]
            if ud['mode'] == 'unknown':
                Clock.unschedule(self._change_touch_mode)
                super(GestureBox, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            else:
                # A gesture was attempted. Did it match?
                gesture = Gesture()
                gesture.add_stroke(
                    zip(touch.ud['gesture_line'].points[::2],
                        touch.ud['gesture_line'].points[1::2]))
                gesture.normalize()
                match = self.gestures.find(gesture, minscore=0.70)
                if match:
                    self.dispatch('on_gesture', match[1].name)
                else:
                    # The gesture wasn't recognized; invoke a normal reaction
                    super(GestureBox, self).on_touch_down(touch)
                    Clock.schedule_once(partial(self._do_touch_up, touch), .1)

                return True

        else:
            if self._touch is not touch and self.uid not in touch.ud:
                super(GestureBox, self).on_touch_up(touch)
        return self._get_uid() in touch.ud

    def _do_touch_up(self, touch, *largs):
        '''(internal) Simulate touch up events for anything that has grabbed the touch'''
        super(GestureBox, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(GestureBox, self).on_touch_up(touch)
        touch.grab_current = None
        return True

    def _change_touch_mode(self, *largs):
        '''(internal) Simulate a touch down if we know the touch did not become
        a gesture'''
        if not self._touch:
            return
        uid = self._get_uid()
        touch = self._touch
        ud = touch.ud[uid]
        if ud['mode'] == 'unknown':
            touch.ungrab(self)
            self._touch = None
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            touch.apply_transform_2d(self.to_parent)
            super(GestureBox, self).on_touch_down(touch)
            touch.pop()
            return

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def on_gesture(self, gesture_name):
        '''Called whenever a gesture has occured. This is a Kivy event. It
        can be overridden in a subclass our bound to using :meth:`Widget.bind`.
        '''
        pass


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.button import Button

    class ExampleApp(App):
        def build(self):
            gesture_box = GestureBox()
            gesture_box.add_gesture("down_swipe",
                'eNq1l91yIkcMhe/nReybpVr/0guwt6nyA6Qcm7Kp3dgUsNns20ejxsyQOGFTruFm4ND9taTTqJvb7ZftHz9WT5vD8dt+M3w+PXdtuH3cwXB383L/++Zm2GG+zQcNh7ubw3H/+mVzyI883H7dyXD7LuSuhg07HVGW83ev25fjOM3HafEv034ZRw076BGMIfzIKYDDuq0EHULBUEJDnMdo/hy/pWH9qa0aIXkDbOZuKk1lOPx2/9/LcC0jw1NfgZ1aCyEEFGaxTPjpjc4t8aq5slm+w+vwSh3sDGcy0DFCz9iwyRyO2IgacUQosf9E6F70ONOhEVh4a4oZIemH6Fj1R3ijE5GGgXCAIIbax+hYdFqIXqaiLEQvV/HsKkZjE5AWLiHK/DF6uYpnV0ExvTQT40am7jP6/9/uVK4SLEQvV4kWoperJAvRy1U6uwpg4gYkmGTlbEQTHZ2lOZulv57LX+8EVK5SLEPncpXPrjZ2x9xsetqa8/2OKKKR1cnCZS9jvU4vV5kWoperfHK1vCP1cPNsxRJp8gwPrOEUEM119Nav48tWtqXw5SvHhO87DjxEoHE6PsM30wAYq5cngPzEppQyVmApfDkrdMaDAUKeUtnEWrbM+QmSpyJLkAJgUFZKrhdHylqRpfBlrdhS+LJWJmsvWrmet/1IT1MMWSU8f89ofBWuZaxOxhIxWqAGs2KeFDrR00vM9bBhU5UceJ1eviotRC9bVRail6tqC9HLVJ1MJTU1b5EAJnKQiU6ei1mwEXgafh1uZapNpvK4J7IjJirQY0Kzg0aY5WbNy1q73iWtHDVaAl122mRnnj6QzLz/knPj4Amed9YIlHyaMFC/zoz/CB72m83L+X5vOl7wzYbbdV6kV21Yq1I+jjvz4X4mYheji61E8RK9XYjSRSgRoovQReyilciti9RFLRFPIs/F1kPKJCYxr29d1LnIPU63WfB5PnfxlBGVKLSK+YvHEaf0isUV+3EXPT2q9OjEip4eYYnSQ4meHlV61E4je3oV2Dq96mJPT3Dsd9NLcwTypUbj8J64FBjfwD3xcmYN5u9M61WoQq1BuzHhF2I3JmIu5joXpbEcAa39bUgrFS5U+WcQ0PBiCL3HpuuUrFjfwc+b7dPzcfwrmf/K1nmXz0kpf98+Hp9LzSqyd/H4+nWzv3952NQXVve5UT/9vn7d7V8fvz10mGdpV5a70iw/RPaqaiSrvwDFYvqM'
                )
            gesture_box.add_gesture("circle",
                'eNq1WNtyGzcMfd8fiV+iIS4EyB9QXzuTD+g4icbxpLU1ttI2f18QoHa5jpy12qlGAyUw9hA4ByQh3dx/vf/z++7u8Hz69nSYfumfxzTdfD7C9OHdw+0fh3fTEe2f9kHT84d3z6enx6+HZ/svTze/H/N0cxHkg4dNR2lQas8fH+8fTu2x0h6rrzz2a4uajhAZtBS+2yOA0z7tCDMkqjk1y0W1pfN3+zNN+/dpl0pGqmdLJcv0/PH25+uwr5Onu74EMxErVLeGMT3fNXQDT4C1kopbLVBhG92LB91Gh6RJinRb5A2ZF8euM/aP5JyxhVVShbBiJW9ho7OPcMZG1YTzWzTP2LgAm8XyBmx0bJqxsfSkm8UqMzaRluVduW5ju5o4qwkKmFWruM28cGLNcW3eriXOWi5kv8zbNK7GcwmbabtP0LXEWcuB7MY3pSVxVuRMiGFJaBOcXEzqYrZtwglLEsluBdOSen7R5LiN7nISzehAwsQZwC3yfwJ3PSnP4FZ31fnNrZX/PS8uKOkCvpBiFkfSF2Sz3PpoC9wVpTqDExXKmkvYmoc274S8nRZ2RXlR1B5u5xGG1bKcK7a5rtz77ILyIihVSVzL2bb8zuB4LefsgnJ+AzjQtTuUXVBeBCVRTKSMbq1HA/u9b7DMohpWSLbPFnZFuf4/6NklzYOki57N1rzAQ8YV/HY3Ztc0L5piXR0BMqAj1GItLmELb/OeXdQ87FKB8QhIOKDXOXGzOb2BGVc1D9sUaNxJNiPM6LQkbpbS9lbKrmpeVAXluRtTTloXdDs2B95z3UYXV1UWVe2aPydutqAO6HIt7+KqCm0f7A2+Fk1JkNyiTQ+b8C6rzJdpyrkoQUlhUx6IZ61XEi8uqyzXKSODTSphAcsAjnBlz4irKvN9CjVxsXEwu2UZ9iopXcmLuqgKWwOMb2JJNoh2y284B9Q11WU6En2NFuRrFVVXVJdhN71QdDhjBIe3a/3xtg3/n54Oh4d5lFdps7zNmjd7Rt2laY9ad3V88XQ6apluW0TxiAL2Yc7qTkqjs6RwSjgxnOBOhpUTw6krJ7kz06up2D3iETUiNB7L7pT+WLZhf3hJi5CIiLyU4zENZ5SlPYWoVSNZTeGMWv25vWnqzhq1amBKYNaotcTjuUdGrSXy8+rMGbWW7E6u66SpRUStJRbgvGZDW0QUXqICjgqqjE6q4dSVM19Yrawi4MJqwUIJyTBqg5TGOpC6F1be9ON6ttdGVkB+XNA2ZYREjwFfCgmSNJKC8/JBjMbyAN0bzLjS5k3dG9RoLJJK95axY9K52KBAohGShBeCAgncdIFcABj79nJI8JHzT0L6/kg/CQk+mFd5Q/BBtKoRZNzXZz4g+MC0YhSCD+hqXWhGgCAn1dcFxWAqdV0uND1gMJWCTIyeBnRy7CtZeLl7KbxRLPaykMObXu1k+1rpIb2VL20Hm9siJFKlTiTqylu7t4SXx31o35ZW3p4zpZVXLyxNsAq5xBIFH/1syH1FCj76Hs69PSn4KHU8k2w+D5aCZ+lbhKLqGvVJF5+i6hp0yRk3WiLFWSedfepdQOMBCtyFl/GsBe5a9xO4r8axESCNh7UNo+GFVw95YB57VHuaHL0Pebwy7DYPb79IevLcex/W3n7/0dobhWI+X1buzVEoytprhcYN/OVwf/fl1H70sql+ry83CbbfxP66/3z64iF2m9sJZxjmPT3+fni6ffh08L9w/IixfkGL68PDb8enx8/fPsVSedrnnc05diDYoIA2CpbUvu7t/gFuoPx3'
                )

            gesture_box.bind(on_gesture=self.gesture)
            button = Button(text="Click here and it gets propogated.\n"
                "Down stroke or draw a circle to invoke a gesture event")

            button.bind(on_press=self.button_press)
            gesture_box.add_widget(button)

            return gesture_box

        def gesture(self, gesture_box, gesture_name):
            print "{0} gesture occured".format(gesture_name)

        def button_press(self, button):
            print "The button got pressed"

    if __name__ == '__main__':
        ExampleApp().run()

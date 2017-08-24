import unittest

from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.base import EventLoop
from kivy.weakproxy import WeakProxy
from kivy.uix.dropdown import DropDown
from kivy.input.motionevent import MotionEvent


KV = Builder.load_string('''
# +/- copied from ActionBar example + edited for the test
FloatLayout:
    ActionBar:
        pos_hint: {'top': 1}
        ActionView:
            use_separator: True
            ActionPrevious:
                title: 'Action Bar'
                with_previous: False
            ActionOverflow:
            ActionButton:
                text: 'Btn0'
                icon: 'atlas://data/images/defaulttheme/audio-volume-high'
            ActionButton:
                text: 'Btn1'
            ActionButton:
                text: 'Btn2'
            ActionGroup:
                id: group1
                text: 'group 1'
                ActionButton:
                    id: group1button
                    text: 'Btn3'
                    on_release:
                        setattr(app, 'g1button', True)
                ActionButton:
                    text: 'Btn4'
            ActionGroup:
                id: group2
                dropdown_width: 200
                text: 'group 2'
                ActionButton:
                    id: group2button
                    text: 'Btn5'
                    on_release:
                        setattr(app, 'g2button', True)
                ActionButton:
                    text: 'Btn6'
                ActionButton:
                    text: 'Btn7'
''')


class My(App):
    def build(self):
        return KV


class UTMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        super(UTMotionEvent, self).depack(args)


class TouchPoint(UTMotionEvent):
    def __init__(self, raw_x, raw_y):
        win = EventLoop.window

        super(UTMotionEvent, self).__init__(
            "unittest", 1, {
                "x": raw_x / float(win.width),
                "y": raw_y / float(win.height),
            }
        )

        # press & release
        EventLoop.post_dispatch_input("begin", self)
        EventLoop.post_dispatch_input("end", self)
        EventLoop.idle()


class Test(unittest.TestCase):
    def check_dropdown(self, present=True):
        any_list = [
            'DropDown' in repr(child) for child in self._win.children
        ]

        # mustn't allow more than one DropDown opened!
        self.assertLess(sum(any_list), 2)

        # passed
        if not present and not any(any_list):
            return
        elif present and any(any_list):
            return

        print('DropDown either missing, or isn\'t supposed to be there')
        self.assertTrue(False)

    def run_test_1_openclose(self, app, *args):
        # click on Group 2 to open its DropDown
        # - DropDown shows up
        # then click away
        # - Group 2 DropDown disappears
        # click on Group 1 to open its DropDown
        # - DropDown shows up
        # then click away
        # - Group 1 DropDown disappears
        group2 = app.root.ids.group2
        group1 = app.root.ids.group1
        EventLoop.idle()

        # no DropDown present yet
        self.check_dropdown(present=False)
        self.assertFalse(group2.is_open)
        self.assertFalse(group1.is_open)

        items = ((group2, group1), (group1, group2))
        for item in items:
            active, passive = item
            # click on active Group
            TouchPoint(*active.center)

            # active Group DropDown shows up
            self.check_dropdown(present=True)
            gdd = WeakProxy(self._win.children[0])

            # active Group DropDown == value in WeakProxy
            self.assertIn(gdd, self._win.children)
            self.assertEqual(gdd, self._win.children[0])
            self.assertTrue(active.is_open)
            self.assertFalse(passive.is_open)

            # click away
            TouchPoint(0, 0)

            # wait for closed active Group DropDown to disappear
            EventLoop.idle()

            # go to the next frame after the DropDown disappeared
            EventLoop.idle()

            # no DropDown is open
            self.assertNotEqual(gdd, self._win.children[0])
            self.assertLess(len(self._win.children), 2)
            self.check_dropdown(present=False)
            self.assertFalse(active.is_open)
            self.assertFalse(passive.is_open)

    def run_test_2_switch(self, app, *args):
        # click on Group 2 to open its DropDown
        # - DropDown shows up
        # then click on Group 1 to open its DropDown
        # - Group 2 DropDown disappears, Group 1 DropDown shows up
        # click away
        # - no DropDown is opened
        group2 = app.root.ids.group2
        group1 = app.root.ids.group1
        EventLoop.idle()

        # no DropDown present yet
        self.check_dropdown(present=False)
        self.assertFalse(group2.is_open)
        self.assertFalse(group1.is_open)

        # click on Group 2
        TouchPoint(*group2.center)

        # Group 2 DropDown shows up
        self.check_dropdown(present=True)
        g2dd = WeakProxy(self._win.children[0])

        # Group 2 DropDown == value in WeakProxy
        self.assertIn(g2dd, self._win.children)
        self.assertEqual(g2dd, self._win.children[0])
        self.assertTrue(group2.is_open)
        self.assertFalse(group1.is_open)

        # click on Group 1
        TouchPoint(*group1.center)

        # wait for closed Group 2 DropDown to disappear
        # and for Group 1 DropDown to appear (there are 2 DDs now)
        EventLoop.idle()

        # go to the next frame after the DropDown disappeared
        EventLoop.idle()

        # Group 1 DropDown != value in WeakProxy (Group 2 DD)
        self.assertNotEqual(g2dd, self._win.children[0])
        self.assertFalse(group2.is_open)
        self.assertTrue(group1.is_open)
        self.check_dropdown(present=True)

        # click away from ActionBar
        TouchPoint(0, 0)

        # wait for closed DropDown to disappear
        EventLoop.idle()

        # go to the next frame after the DropDown disappeared
        EventLoop.idle()

        # no DropDown present in Window
        self.check_dropdown(present=False)
        self.assertFalse(group2.is_open)
        self.assertFalse(group1.is_open)
        self.assertNotIn(g2dd, self._win.children)

    def run_test_3_openpress(self, app, *args):
        # click on Group 2 to open its DropDown
        # - DropDown shows up
        # then click on Group 2 DropDown button
        # - DropDown disappears
        # click on Group 1 to open its DropDown
        # - DropDown shows up
        # then click on Group 1 DropDown button
        # - DropDown disappears
        group2 = app.root.ids.group2
        group2button = app.root.ids.group2button
        group1 = app.root.ids.group1
        group1button = app.root.ids.group1button
        EventLoop.idle()

        # no DropDown present yet
        self.check_dropdown(present=False)
        self.assertFalse(group2.is_open)
        self.assertFalse(group1.is_open)

        items = (
            (group2, group1, group2button),
            (group1, group2, group1button)
        )
        for item in items:
            active, passive, button = item

            # click on active Group
            TouchPoint(*active.center)

            # active Group DropDown shows up
            self.check_dropdown(present=True)
            gdd = WeakProxy(self._win.children[0])

            # active Group DropDown == value in WeakProxy
            self.assertIn(gdd, self._win.children)
            self.assertEqual(gdd, self._win.children[0])
            self.assertTrue(active.is_open)
            self.assertFalse(passive.is_open)

            # click on active Group DropDown Button (needed to_window)
            TouchPoint(*button.to_window(*button.center))
            self.assertTrue(getattr(
                app, active.text[0::6] + 'button'
            ))

            # wait for closed active Group DropDown to disappear
            EventLoop.idle()

            # go to the next frame after the DropDown disappeared
            EventLoop.idle()

            # no DropDown is open
            self.assertNotEqual(gdd, self._win.children[0])
            self.assertLess(len(self._win.children), 2)
            self.assertFalse(active.is_open)
            self.assertFalse(passive.is_open)
            self.check_dropdown(present=False)

    def run_test_4_openmulti(self, app, *args):
        # click on Group to open its DropDown
        # - DropDown shows up
        # then click on Group DropDown button
        # - DropDown disappears
        # repeat
        group2 = app.root.ids.group2
        group2button = app.root.ids.group2button
        group1 = app.root.ids.group1
        group1button = app.root.ids.group1button
        EventLoop.idle()

        # no DropDown present yet
        self.check_dropdown(present=False)
        self.assertFalse(group2.is_open)

        items = ((group2, group2button), (group1, group1button))
        for item in items:
            group, button = item

            for _ in range(5):
                # click on Group
                TouchPoint(*group.center)

                # Group DropDown shows up
                self.check_dropdown(present=True)
                gdd = WeakProxy(self._win.children[0])

                # Group DropDown == value in WeakProxy
                self.assertIn(gdd, self._win.children)
                self.assertEqual(gdd, self._win.children[0])
                self.assertTrue(group.is_open)

                # click on Group DropDown Button (FIX!!!!!)
                TouchPoint(*button.to_window(*button.center))

                # wait for closed Group DropDown to disappear
                EventLoop.idle()

                # go to the next frame after the DropDown disappeared
                EventLoop.idle()

                # Group 1 DropDown != value in WeakProxy (Group 2 DD)
                self.assertNotEqual(gdd, self._win.children[0])
                self.assertFalse(group.is_open)
                self.check_dropdown(present=False)

    def run_test_example(self, app, *args):
        self._win = EventLoop.window
        self.run_test_1_openclose(app)
        self.run_test_2_switch(app)
        self.run_test_3_openpress(app)
        self.run_test_4_openmulti(app)
        app.stop()

    def test_example(self):
        app = My()
        p = partial(self.run_test_example, app)
        Clock.schedule_once(p, 0)
        app.run()

if __name__ == '__main__':
    unittest.main()

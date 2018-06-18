from kivy.tests.common import GraphicUnitTest

from kivy.base import EventLoop
from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.uix.dropdown import DropDown
from kivy.uix.actionbar import ActionBar, ActionView, ContextualActionView, \
    ActionPrevious, ActionBarException, ActionOverflow
from kivy.uix.widget import Widget
from kivy.weakproxy import WeakProxy


KV = '''
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
                text: 'Btn2 & some text to collapse the groups'
            ActionGroup:
                id: group1
                text: 'group 1'
                ActionButton:
                    id: group1button
                    text: 'Btn3'
                    on_release:
                        setattr(root, 'g1button', True)
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
                        setattr(root, 'g2button', True)
                ActionButton:
                    text: 'Btn6'
                ActionButton:
                    text: 'Btn7'
'''


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


class ActionBarTestCase(GraphicUnitTest):
    framecount = 0

    def setUp(self):
        # kill KV lang logging (too long test)
        import kivy.lang.builder as builder

        if not hasattr(self, '_trace'):
            self._trace = builder.trace

        self.builder = builder
        builder.trace = lambda *_, **__: None
        super(ActionBarTestCase, self).setUp()

    def tearDown(self):
        # add the logging back
        import kivy.lang.builder as builder
        builder.trace = self._trace
        super(ActionBarTestCase, self).tearDown()

    def move_frames(self, t):
        for i in range(t):
            EventLoop.idle()

    def clean_garbage(self, *args):
        for child in self._win.children[:]:
            self._win.remove_widget(child)
        self.move_frames(5)

    def check_dropdown(self, present=True):
        any_list = [
            isinstance(child, DropDown)
            for child in self._win.children
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

    def test_1_openclose(self, *args):
        # click on Group 2 to open its DropDown
        # - DropDown shows up
        # then click away
        # - Group 2 DropDown disappears
        # click on Group 1 to open its DropDown
        # - DropDown shows up
        # then click away
        # - Group 1 DropDown disappears
        self._win = EventLoop.window
        self.clean_garbage()
        root = Builder.load_string(KV)
        self.render(root)
        self.assertLess(len(self._win.children), 2)
        group2 = root.ids.group2
        group1 = root.ids.group1
        self.move_frames(5)

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

            # wait for closed Group DropDown to disappear
            # go to the next frame after the DropDown disappeared
            self.move_frames(5)

            # no DropDown is open
            self.assertNotEqual(gdd, self._win.children[0])
            self.assertLess(len(self._win.children), 2)
            self.check_dropdown(present=False)
            self.assertFalse(active.is_open)
            self.assertFalse(passive.is_open)
        self._win.remove_widget(root)

    def test_2_switch(self, *args):
        # click on Group 2 to open its DropDown
        # - DropDown shows up
        # then click on Group 1 to open its DropDown
        # - Group 2 DropDown disappears, Group 1 DropDown shows up
        # click away
        # - no DropDown is opened
        self._win = EventLoop.window
        self.clean_garbage()
        root = Builder.load_string(KV)
        self.render(root)
        self.assertLess(len(self._win.children), 2)
        group2 = root.ids.group2
        group1 = root.ids.group1
        self.move_frames(5)

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
        # go to the next frame after the DropDown disappeared
        self.move_frames(5)

        # Group 1 DropDown != value in WeakProxy (Group 2 DD)
        self.assertNotEqual(g2dd, self._win.children[0])
        self.assertFalse(group2.is_open)
        self.assertTrue(group1.is_open)
        self.check_dropdown(present=True)

        # click away from ActionBar
        TouchPoint(0, 0)

        # wait for closed Group DropDown to disappear
        # go to the next frame after the DropDown disappeared
        self.move_frames(5)

        # no DropDown present in Window
        self.check_dropdown(present=False)
        self.assertFalse(group2.is_open)
        self.assertFalse(group1.is_open)
        self.assertNotIn(g2dd, self._win.children)
        self._win.remove_widget(root)

    def test_3_openpress(self, *args):
        # click on Group 2 to open its DropDown
        # - DropDown shows up
        # then click on Group 2 DropDown button
        # - DropDown disappears
        # click on Group 1 to open its DropDown
        # - DropDown shows up
        # then click on Group 1 DropDown button
        # - DropDown disappears
        self._win = EventLoop.window
        self.clean_garbage()
        root = Builder.load_string(KV)
        self.render(root)
        self.assertLess(len(self._win.children), 2)
        group2 = root.ids.group2
        group2button = root.ids.group2button
        group1 = root.ids.group1
        group1button = root.ids.group1button
        self.move_frames(5)

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
                root, active.text[0::6] + 'button'
            ))

            # wait for closed Group DropDown to disappear
            # go to the next frame after the DropDown disappeared
            self.move_frames(5)

            # no DropDown is open
            self.assertNotEqual(gdd, self._win.children[0])
            self.assertLess(len(self._win.children), 2)
            self.assertFalse(active.is_open)
            self.assertFalse(passive.is_open)
            self.check_dropdown(present=False)
        self._win.remove_widget(root)

    def test_4_openmulti(self, *args):
        # click on Group to open its DropDown
        # - DropDown shows up
        # then click on Group DropDown button
        # - DropDown disappears
        # repeat
        self._win = EventLoop.window
        self.clean_garbage()
        root = Builder.load_string(KV)
        self.render(root)
        self.assertLess(len(self._win.children), 2)
        group2 = root.ids.group2
        group2button = root.ids.group2button
        group1 = root.ids.group1
        group1button = root.ids.group1button
        self.move_frames(5)

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

                # click on Group DropDown Button
                TouchPoint(*button.to_window(*button.center))

                # wait for closed Group DropDown to disappear
                # go to the next frame after the DropDown disappeared
                self.move_frames(5)

                # no DropDown is open
                self.assertNotEqual(gdd, self._win.children[0])
                self.assertFalse(group.is_open)
                self.check_dropdown(present=False)
        self._win.remove_widget(root)

    def test_5_action_view(self):
        self._win = EventLoop.window
        self.clean_garbage()
        root = Builder.load_string(KV)
        self.render(root)
        self.assertLess(len(self._win.children), 2)
        action_bar = root.children[0]
        action_view = action_bar.children[0]
        action_previous = action_view.action_previous
        self.assertIsInstance(action_bar, ActionBar)
        self.assertIsInstance(action_view, ActionView)
        self.assertIsInstance(action_previous, ActionPrevious)
        self.move_frames(5)

        # General
        # -------
        # integrity checks on the KV loaded subtree:
        self.assertSequenceEqual(action_bar.children, [action_view])
        self.assertIs(action_view.parent, action_bar)
        self.assertIsInstance(action_view.overflow_group, ActionOverflow)
        # add_widget() behavior:
        self.assertRaises(ActionBarException,
                          action_view.add_widget, Widget())  # not an ActionItem
        with self.assertRaises(ValueError):
            action_bar.action_view = None  # action_view can't be removed
        with self.assertRaises(ValueError):
            action_bar.remove_widget(action_view)  # same here
        self.assertIs(action_bar.action_view, action_view)
        with self.assertRaises(ActionBarException):
            action_bar.action_view = ContextualActionView()  # not allowed
        self.assertIs(action_bar.action_view, action_view)
        # adding another ActionView replaces the existing one:
        action_view2 = ActionView()
        action_bar.add_widget(action_view2)
        self.assertIs(action_bar.action_view, action_view2)
        self.assertSequenceEqual(action_bar.children, [action_view2])
        self.assertIs(action_view2.parent, action_bar)
        self.assertIsNone(action_view.parent)
        # readding/-setting results in no change:
        action_bar.add_widget(action_view2)
        self.assertIs(action_bar.action_view, action_view2)
        self.assertSequenceEqual(action_bar.children, [action_view2])
        action_bar.action_view = action_view2
        self.assertIs(action_bar.action_view, action_view2)
        self.assertSequenceEqual(action_bar.children, [action_view2])
        # resetting to the original one does, however:
        action_bar.action_view = action_view
        self.assertIs(action_bar.action_view, action_view)
        self.assertSequenceEqual(action_bar.children, [action_view])
        self.assertIs(action_view.parent, action_bar)
        self.assertIsNone(action_view2.parent)

        # ActionPrevious
        # --------------
        with self.assertRaises(ValueError):
            action_view.action_previous = Widget()  # must be ActionPrevious
        with self.assertRaises(ValueError):
            action_view.action_previous = None  # action_view can't be removed
        self.assertIs(action_view.action_previous, action_previous)
        # check the property but not the children here, it
        # may only be added to children during layouting:
        new_action_previous = ActionPrevious()
        action_view.add_widget(new_action_previous)
        self.assertIs(action_view.action_previous, new_action_previous)
        action_view.add_widget(action_previous)
        self.assertIs(action_view.action_previous, action_previous)
        # action_previous is initially unassigned:
        action_view3 = ActionView()
        self.assertIs(action_view3.action_previous, None)

    def test_6_contextual_action_views(self):
        self._win = EventLoop.window
        self.clean_garbage()
        root = Builder.load_string(KV)
        self.render(root)
        self.assertLess(len(self._win.children), 2)
        action_bar = root.children[0]
        action_view = action_bar.children[0]
        self.assertIsInstance(action_bar, ActionBar)
        self.assertIsInstance(action_view, ActionView)
        stack_cont_action_view = action_bar._stack_cont_action_view

        # General
        # -------
        cont_action_view = ContextualActionView()
        action_previous = ActionPrevious(title='ContextualActionView')
        self.assertIsNone(cont_action_view.action_previous)
        cont_action_view.add_widget(action_previous)
        self.assertIs(cont_action_view.action_previous, action_previous)
        self.assertRaises(ActionBarException,
                          action_bar.add_widget, Widget())

        # ActionBar only has a single (Contextual)ActionView child at a time
        # ------------------------------------------------------------------
        self.assertSequenceEqual(action_bar.children, [action_view])
        action_bar.add_widget(cont_action_view)
        self.assertIs(cont_action_view.parent, action_bar)
        self.assertIn(cont_action_view, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [cont_action_view])
        action_bar.remove_widget(cont_action_view)
        self.assertIsNone(cont_action_view.parent)
        self.assertNotIn(cont_action_view, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [action_view])
        # now with several:
        action_bar.add_widget(cont_action_view)
        self.assertIn(cont_action_view, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [cont_action_view])
        cont_action_view2 = ContextualActionView()
        cont_action_view2.action_previous = ActionPrevious()
        action_view2 = ActionView()
        action_view2.action_previous = ActionPrevious()
        action_bar.add_widget(cont_action_view2)
        self.assertIn(cont_action_view2, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [cont_action_view2])
        action_bar.add_widget(action_view2)
        # ContextualActionViews hide ActionView changes:
        self.assertSequenceEqual(action_bar.children, [cont_action_view2])
        action_bar.action_view = action_view
        self.assertSequenceEqual(action_bar.children, [cont_action_view2])
        # action_previous event removes ContextualActionViews, and only them:
        action_bar._emit_previous(action_bar)
        self.assertNotIn(cont_action_view2, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [cont_action_view])
        action_bar._emit_previous(action_bar)
        self.assertNotIn(cont_action_view, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [action_view])
        action_bar._emit_previous(action_bar)
        self.assertSequenceEqual(action_bar.children, [action_view])
        # remove an intermediate ContextualActionView:
        action_bar.add_widget(cont_action_view2)
        self.assertIn(cont_action_view2, stack_cont_action_view)
        action_bar.add_widget(cont_action_view)
        self.assertIn(cont_action_view, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [cont_action_view])
        action_bar.remove_widget(cont_action_view2)
        self.assertNotIn(cont_action_view2, stack_cont_action_view)
        self.assertIn(cont_action_view, stack_cont_action_view)
        self.assertSequenceEqual(action_bar.children, [cont_action_view])
        action_bar.remove_widget(cont_action_view)  # reset for the next tests
        
        # Automatic ActionPrevious button binding
        #----------------------------------------
        ap_button_center = action_view.action_previous.ids.button.center[:]
        action_bar.add_widget(cont_action_view)
        action_bar.add_widget(cont_action_view2)
        self.move_frames(5)
        self.assertSequenceEqual(action_bar.children, [cont_action_view2])
        TouchPoint(*ap_button_center)
        self.move_frames(5)
        self.assertSequenceEqual(action_bar.children, [cont_action_view])
        TouchPoint(*ap_button_center)
        self.move_frames(5)
        self.assertSequenceEqual(action_bar.children, [action_view])
        TouchPoint(*ap_button_center)  # ActionView's button isn't bound, though
        self.move_frames(5)
        self.assertSequenceEqual(action_bar.children, [action_view])


if __name__ == '__main__':
    import unittest
    unittest.main()

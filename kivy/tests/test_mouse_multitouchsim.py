from kivy.tests.common import GraphicUnitTest


class MultitouchSimulatorTestCase(GraphicUnitTest):

    framecount = 3

    def render(self, root, framecount=1):
        pass

    # helper methods
    def correct_y(self, win, y):
        # flip, because the mouse provider uses system's
        # raw one and it's changed to bottom-left origin
        # with Window's system_size[1] for 'mouse_pos'
        return win.height - 1.0 - y

    def mouse_init(self, on_demand=False, disabled=False, scatter=False):
        # prepare MouseMotionEventProvider
        # and widget it interacts with
        from kivy.base import EventLoop
        from kivy.uix.button import Button
        from kivy.uix.scatter import Scatter

        eventloop = EventLoop
        win = eventloop.window
        eventloop.idle()
        wid = Scatter() if scatter else Button()

        if on_demand:
            mode = 'multitouch_on_demand'
        elif disabled:
            mode = 'disable_multitouch'
        else:
            mode = ''
        from kivy.input.providers.mouse import MouseMotionEventProvider
        mouse = MouseMotionEventProvider('unittest', mode)
        mouse.is_touch = True

        # defaults from ME, it's missing because we use
        # the provider directly instead of ME
        mouse.scale_for_screen = lambda *_, **__: None
        mouse.grab_exclusive_class = None
        mouse.grab_list = []

        if on_demand:
            self.assertTrue(mouse.multitouch_on_demand)
        return (eventloop, win, mouse, wid)

    def multitouch_dot_touch(self, button, **kwargs):
        # touch -> dot appears -> touch again -> dot disappears
        eventloop, win, mouse, wid = self.mouse_init(**kwargs)

        # register mouse provider
        mouse.start()
        eventloop.add_input_provider(mouse)

        # no mouse touch anywhere
        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # right button down, red dot should appear
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'right', {}
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)

        if 'on_demand' in kwargs and 'scatter' not in kwargs:
            # doesn't do anything on a pure Button
            self.render(wid)

            # cleanup!
            # remove mouse provider
            mouse.stop()
            eventloop.remove_input_provider(mouse)
            return

        elif 'on_demand' in kwargs and 'scatter' in kwargs:
            self.assertIn(
                'multitouch_sim',
                mouse.touches[event_id].profile
            )
            self.assertTrue(mouse.multitouch_on_demand)

            # multitouch_sim is changed in on_touch_down
            # method of the widget that's able to handle
            # multiple touches, therefore for Scatter we
            # need to dispatch the method and because we
            # triggered only on_mouse_down directly i.e.
            # without ME dispatch, on_touch_down was not
            # called == multitouch_sim is False
            self.advance_frames(1)  # initialize stuff
            wid.on_touch_down(mouse.touches[event_id])
            wid.on_touch_up(mouse.touches[event_id])
            self.assertTrue(mouse.touches[event_id].multitouch_sim)

        elif 'disabled' in kwargs:
            self.assertIsNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot isn't present

        else:
            self.assertIsNotNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot is present

        # XXX right button up
        # first release the touch then check, so that we
        # have the red dot drawn in on_demand and in the
        # default (multitouch everywhere) because in the
        # multitouch_on_demand is the circle drawn after
        # the touch is released (in on_mouse_release)
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'right', {}
        )

        self.assertEqual(mouse.counter, 1)

        # because the red dot is removed by the left button
        if 'disabled' not in kwargs:
            self.assertIn(event_id, mouse.touches)
            self.assertIsNotNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot is present

        # button is down on the previous dot's position
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            button, {}
        )
        # if the multitouch is disabled, the touch event
        # increments the counter
        self.assertEqual(
            mouse.counter,
            1 + int('disabled' in kwargs)
        )
        if 'disabled' in kwargs:
            # the right click is ignored, test ends here
            self.assertNotIn(
                event_id, mouse.touches
            )
            # cleanup!
            # remove mouse provider
            mouse.stop()
            eventloop.remove_input_provider(mouse)
            return
        else:
            self.assertIsNotNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot is present

        # ellipse proxy (<3 #1318 Instruction.proxy_ref)
        dot_proxy = mouse.touches[
            event_id
        ].ud.get('_drawelement')[1].proxy_ref

        # the dot is removed after the touch is released
        # when right - touch is preserved -> dot remains
        # when left  - touch is destroyed -> dot removed
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            button, {}
        )  # no matter where

        # the touch, which holds the only ref to the dot
        # instance (Ellipse) is collected, therefore the
        # proxy can confirm the dot is removed
        # (indirect ref at least + it would be nasty for
        # checking if the ellipse remained on visible on
        # the Canvas after being GC-ed if not impossible
        # without the Instruction object trick ._. )
        if button == 'left':
            with self.assertRaises(ReferenceError):
                print(dot_proxy)

            self.assertEqual(mouse.counter, 1)
            self.assertNotIn(event_id, mouse.touches)
            self.assertEqual(mouse.touches, {})

        elif button == 'right':
            self.assertEqual(mouse.counter, 1)
            self.assertIn(event_id, mouse.touches)
            self.assertIsNotNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot is present

        self.render(wid)

        # cleanup!
        # remove mouse provider
        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def multitouch_dot_move(self, button, **kwargs):
        # touch -> dot appears -> move touch -> dot moves
        # -> release touch -> touch & dot disappear
        eventloop, win, mouse, wid = self.mouse_init(**kwargs)

        # register mouse provider
        mouse.start()
        eventloop.add_input_provider(mouse)

        # no mouse touch anywhere
        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # right button down, red dot should appear
        # if the 'multitouch_on_demand' is disabled
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'right', {}
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)

        if 'on_demand' in kwargs and 'scatter' not in kwargs:
            # doesn't do anything on a pure Button
            self.render(wid)

            # cleanup!
            # remove mouse provider
            mouse.stop()
            eventloop.remove_input_provider(mouse)
            return

        # XXX right button up
        # first release the touch then check, so that we
        # have the red dot drawn in on_demand and in the
        # default (multitouch everywhere) because in the
        # multitouch_on_demand is the circle drawn after
        # the touch is released (in on_mouse_release)
        elif 'on_demand' in kwargs and 'scatter' in kwargs:
            # on_demand works after the touch is up
            self.assertIn(
                'multitouch_sim',
                mouse.touches[event_id].profile
            )
            self.assertTrue(mouse.multitouch_on_demand)

            # multitouch_sim is changed in on_touch_down
            # method of the widget that's able to handle
            # multiple touches, therefore for Scatter we
            # need to dispatch the method and because we
            # triggered only on_mouse_down directly i.e.
            # without ME dispatch, on_touch_down was not
            # called == multitouch_sim is False
            self.advance_frames(1)  # initialize stuff
            wid.on_touch_down(mouse.touches[event_id])
            wid.on_touch_up(mouse.touches[event_id])
            self.assertTrue(mouse.touches[event_id].multitouch_sim)

            win.dispatch(
                'on_mouse_up',
                10, self.correct_y(win, 10),
                'right', {}
            )
            ellipse = mouse.touches[
                event_id
            ].ud.get('_drawelement')[1].proxy_ref
            win.dispatch(
                'on_mouse_down',
                10, self.correct_y(win, 10),
                'right', {}
            )

        elif 'disabled' in kwargs:
            self.assertIsNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot isn't present

        else:
            self.assertIsNotNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot is present

        # do NOT make any hard refs to '_drawelement'
        if 'disabled' in kwargs:
            # the right click doesn't draw the red dot
            # the instructions aren't present, test ends
            self.assertIsNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot isn't present
            # cleanup!
            # remove mouse provider
            mouse.stop()
            eventloop.remove_input_provider(mouse)
            return

        else:
            ellipse = mouse.touches[
                event_id
            ].ud.get('_drawelement')[1].proxy_ref

        # the red dot moves when the touch is moving
        win.dispatch(
            'on_mouse_move',
            11, self.correct_y(win, 11),
            {}
        )
        self.assertEqual(
            ellipse.pos,
            (1, 1)
        )  # bounding box from Rectangle, R=10 -> 20 width

        # right button up
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'right', {}
        )
        self.assertEqual(mouse.counter, 1)

        # because the red dot is removed by the left button
        self.assertIn(event_id, mouse.touches)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # the red dot is present

        # the dot is at (11, 11), but the touch is in
        # its bounding box, therefore it can move it
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            button, {}
        )

        # manipulating already existing touch,
        # no new one was created
        self.assertEqual(mouse.counter, 1)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # the red dot is present

        # the red dot moves when the touch is moving
        win.dispatch(
            'on_mouse_move',
            50, self.correct_y(win, 50),
            {}
        )
        self.assertEqual(
            ellipse.pos,
            (40, 40)
        )  # bounding box from Rectangle, R=10 -> 20 width

        # the dot is removed after the touch is released
        # when right - touch is preserved -> dot remains
        # when left  - touch is destroyed -> dot removed
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            button, {}
        )  # no matter where
        self.assertEqual(mouse.counter, 1)

        if button == 'left':
            self.assertNotIn(event_id, mouse.touches)
        elif button == 'right':
            self.assertIn(event_id, mouse.touches)
            self.assertIsNotNone(
                mouse.touches[event_id].ud.get('_drawelement')
            )  # the red dot is present

        self.render(wid)

        # cleanup!
        # remove mouse provider
        mouse.stop()
        eventloop.remove_input_provider(mouse)

    # tests
    def test_multitouch_dontappear(self):
        eventloop, win, mouse, wid = self.mouse_init()

        # register mouse provider
        mouse.start()
        eventloop.add_input_provider(mouse)

        # no mouse touch anywhere
        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # left button down
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'left', {}
        )
        event_id = next(iter(mouse.touches))
        win.dispatch(
            'on_mouse_move',
            11, self.correct_y(win, 11),
            {}
        )
        self.assertEqual(mouse.counter, 1)
        self.assertIsNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # the red dot isn't present

        # left button up
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'left', {}
        )
        # after the releasing the touch disappears,
        # but the counter remains
        self.assertEqual(mouse.counter, 1)
        self.assertNotIn(event_id, mouse.touches)

        self.advance_frames(1)
        self.render(wid)

        # cleanup!
        # remove mouse provider
        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_multitouch_appear(self):
        eventloop, win, mouse, wid = self.mouse_init()

        # register mouse provider
        mouse.start()
        eventloop.add_input_provider(mouse)

        # no mouse touch anywhere
        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # right button down, red dot should appear
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'right', {}
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # the red dot is present

        # do NOT make any hard refs to '_drawelement'
        ellipse = mouse.touches[
            event_id
        ].ud.get('_drawelement')[1].proxy_ref

        # check ellipse's position
        self.assertAlmostEqual(ellipse.pos[0], 0, delta=0.0001)
        # bounding box from Rectangle, R=10 -> 20 width
        # almost equal because the correct_y uses the same
        # float - float, which returns decimal garbage
        self.assertAlmostEqual(ellipse.pos[1], 0, delta=0.0001)

        win.dispatch(
            'on_mouse_move',
            11, self.correct_y(win, 11),
            {}
        )
        # the red dot moves when the touch is moving
        self.assertEqual(
            ellipse.pos,
            (1, 1)
        )  # bounding box from Rectangle, R=10 -> 20 width
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'right', {}
        )

        self.assertEqual(
            ellipse.pos,
            (1, 1)
        )  # bounding box from Rectangle, R=10 -> 20 width
        self.assertEqual(mouse.counter, 1)
        # because the red dot is removed by the left button
        self.assertIn(event_id, mouse.touches)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # the red dot is present

        self.render(wid)

        # cleanup!
        # remove mouse provider
        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_multitouch_dot_lefttouch(self):
        self.multitouch_dot_touch('left')

    def test_multitouch_dot_leftmove(self):
        self.multitouch_dot_move('left')

    def test_multitouch_dot_righttouch(self):
        self.multitouch_dot_touch('right')

    def test_multitouch_dot_rightmove(self):
        self.multitouch_dot_move('right')

    def test_multitouch_on_demand_noscatter_lefttouch(self):
        self.multitouch_dot_touch('left', on_demand=True)

    def test_multitouch_on_demand_noscatter_leftmove(self):
        self.multitouch_dot_move('left', on_demand=True)

    def test_multitouch_on_demand_noscatter_righttouch(self):
        self.multitouch_dot_touch('right', on_demand=True)

    def test_multitouch_on_demand_noscatter_rightmove(self):
        self.multitouch_dot_move('right', on_demand=True)

    def test_multitouch_on_demand_scatter_lefttouch(self):
        self.multitouch_dot_touch(
            'left', on_demand=True, scatter=True
        )

    def test_multitouch_on_demand_scatter_leftmove(self):
        self.multitouch_dot_move(
            'left', on_demand=True, scatter=True
        )

    def test_multitouch_on_demand_scatter_righttouch(self):
        self.multitouch_dot_touch(
            'right', on_demand=True, scatter=True
        )

    def test_multitouch_on_demand_scatter_rightmove(self):
        self.multitouch_dot_move(
            'right', on_demand=True, scatter=True
        )

    def test_multitouch_disabled_lefttouch(self):
        self.multitouch_dot_touch('left', disabled=True)

    def test_multitouch_disabled_leftmove(self):
        self.multitouch_dot_move('left', disabled=True)

    def test_multitouch_disabled_righttouch(self):
        self.multitouch_dot_touch('right', disabled=True)

    def test_multitouch_disabled_rightmove(self):
        self.multitouch_dot_move('right', disabled=True)

    def test_ctrl_left_multitouch_enabled(self):
        # ctrl + left click creates a multitouch dot when multitouch is enabled,
        # behaving identically to a right-click
        eventloop, win, mouse, wid = self.mouse_init()

        mouse.start()
        eventloop.add_input_provider(mouse)

        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # ctrl + left button down: red dot should appear
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'left', ['ctrl']
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # the red dot is present

        # ctrl + left button up: dot should persist (same as right-click)
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'left', ['ctrl']
        )
        self.assertEqual(mouse.counter, 1)
        self.assertIn(event_id, mouse.touches)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # red dot persists after button release

        self.render(wid)

        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_ctrl_left_multitouch_disabled(self):
        # ctrl + left click with disable_multitouch creates a plain touch
        # with no red dot, and the touch is removed on button release
        eventloop, win, mouse, wid = self.mouse_init(disabled=True)

        mouse.start()
        eventloop.add_input_provider(mouse)

        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # ctrl + left button down: no red dot because multitouch is disabled
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'left', ['ctrl']
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)
        self.assertIsNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # no red dot

        # left button up: touch is removed
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'left', ['ctrl']
        )
        self.assertEqual(mouse.counter, 1)
        self.assertNotIn(event_id, mouse.touches)

        self.render(wid)

        mouse.stop()
        eventloop.remove_input_provider(mouse)


    def test_button_all_removes_all_touches(self):
        # button='all' in on_mouse_release (sent by Numpad 0 / Fn on Windows)
        # must remove every live touch without crashing — this is the scenario
        # reported in issue #9289
        eventloop, win, mouse, wid = self.mouse_init()

        mouse.start()
        eventloop.add_input_provider(mouse)

        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        # start a left-button drag
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'left', {}
        )
        self.assertEqual(mouse.counter, 1)
        self.assertEqual(len(mouse.touches), 1)

        win.dispatch(
            'on_mouse_move',
            20, self.correct_y(win, 20),
            {}
        )

        # Numpad 0 / Fn triggers button='all' — all touches must be cleared
        win.dispatch(
            'on_mouse_up',
            20, self.correct_y(win, 20),
            'all', {}
        )
        self.assertEqual(len(mouse.touches), 0)
        self.assertIsNone(mouse.current_drag)

        self.render(wid)

        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_button_all_with_multitouch_dot(self):
        # button='all' must also clear a live multitouch simulation dot
        eventloop, win, mouse, wid = self.mouse_init()

        mouse.start()
        eventloop.add_input_provider(mouse)

        # place a multitouch dot with right-click
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'right', {}
        )
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'right', {}
        )
        self.assertEqual(len(mouse.touches), 1)

        # button='all' must clear the sticky dot too
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'all', {}
        )
        self.assertEqual(len(mouse.touches), 0)
        self.assertIsNone(mouse.current_drag)

        self.render(wid)

        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_modifiers_in_touch_profile(self):
        # 'modifiers' must be declared in the profile for every touch type
        eventloop, win, mouse, wid = self.mouse_init()

        mouse.start()
        eventloop.add_input_provider(mouse)

        for button, modifiers in [
            ('left', {}),
            ('right', {}),
            ('left', ['ctrl']),
        ]:
            win.dispatch(
                'on_mouse_down',
                10, self.correct_y(win, 10),
                button, modifiers
            )
            event_id = next(iter(mouse.touches))
            self.assertIn('modifiers', mouse.touches[event_id].profile)
            win.dispatch(
                'on_mouse_up',
                10, self.correct_y(win, 10),
                button, modifiers
            )

        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_touch_modifiers_updated(self):
        # touch.modifiers must reflect the modifiers at press time and
        # be updated with each subsequent mouse-move event
        eventloop, win, mouse, wid = self.mouse_init()

        mouse.start()
        eventloop.add_input_provider(mouse)

        # press with ctrl held
        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'left', ['ctrl']
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.touches[event_id].modifiers, ['ctrl'])

        # move with shift held — modifiers must update
        win.dispatch(
            'on_mouse_move',
            20, self.correct_y(win, 20),
            ['shift']
        )
        self.assertEqual(mouse.touches[event_id].modifiers, ['shift'])

        # move with no modifiers
        win.dispatch(
            'on_mouse_move',
            30, self.correct_y(win, 30),
            []
        )
        self.assertEqual(mouse.touches[event_id].modifiers, [])

        win.dispatch(
            'on_mouse_up',
            30, self.correct_y(win, 30),
            'left', []
        )

        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_middle_button_multitouch_enabled(self):
        # middle click creates a multitouch dot, behaving like right-click
        eventloop, win, mouse, wid = self.mouse_init()

        mouse.start()
        eventloop.add_input_provider(mouse)

        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'middle', {}
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # red dot present

        # middle button up: dot persists (same as right-click)
        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'middle', {}
        )
        self.assertEqual(mouse.counter, 1)
        self.assertIn(event_id, mouse.touches)
        self.assertIsNotNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # dot still present after release

        self.render(wid)

        mouse.stop()
        eventloop.remove_input_provider(mouse)

    def test_middle_button_multitouch_disabled(self):
        # middle click with disable_multitouch creates a plain touch, no dot
        eventloop, win, mouse, wid = self.mouse_init(disabled=True)

        mouse.start()
        eventloop.add_input_provider(mouse)

        self.assertEqual(mouse.counter, 0)
        self.assertEqual(mouse.touches, {})

        win.dispatch(
            'on_mouse_down',
            10, self.correct_y(win, 10),
            'middle', {}
        )
        event_id = next(iter(mouse.touches))
        self.assertEqual(mouse.counter, 1)
        self.assertIsNone(
            mouse.touches[event_id].ud.get('_drawelement')
        )  # no red dot

        win.dispatch(
            'on_mouse_up',
            10, self.correct_y(win, 10),
            'middle', {}
        )
        self.assertEqual(mouse.counter, 1)
        self.assertNotIn(event_id, mouse.touches)

        self.render(wid)

        mouse.stop()
        eventloop.remove_input_provider(mouse)


if __name__ == '__main__':
    import unittest
    unittest.main()

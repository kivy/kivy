from kivy.tests.common import GraphicUnitTest


class MouseHoverEventTestCase(GraphicUnitTest):
    '''Tests hover event from `MouseMotionEventProvider`.
    '''

    def setUp(self):
        super().setUp()
        self.etype = None
        self.motion_event = None
        self.touch_event = None
        self.button_widget = None
        from kivy.input.providers.mouse import MouseMotionEventProvider
        self.mouse = mouse = MouseMotionEventProvider('mouse', '')
        from kivy.base import EventLoop
        win = EventLoop.window
        self.old_mouse_pos = win.mouse_pos[:]
        self.old_rotation = win.rotation
        self.old_system_size = win.system_size[:]
        win.mouse_pos = (0.0, 0.0)
        win.rotation = 0
        win.system_size = (320, 240)
        mouse.start()
        EventLoop.add_input_provider(mouse)
        win.fbind('on_motion', self.on_motion)
        # Patch `win.on_close` method to prevent EventLoop from removing
        # window from event listeners list.
        self.old_on_close = win.on_close
        win.on_close = lambda *args: None

    def tearDown(self, *args, **kwargs):
        self.etype = None
        self.motion_event = None
        self.touch_event = None
        from kivy.base import EventLoop
        win = EventLoop.window
        win.mouse_pos = self.old_mouse_pos
        win.rotation = self.old_rotation
        win.old_system_size = self.old_system_size
        self.old_mouse_pos = None
        self.old_rotation = None
        self.old_system_size = None
        if self.button_widget:
            win.remove_widget(self.button_widget)
            self.button_widget = None
        mouse = self.mouse
        mouse.stop()
        EventLoop.remove_input_provider(mouse)
        self.mouse = None
        win.funbind('on_motion', self.on_motion)
        # Restore method `on_close` to window
        win.on_close = self.old_on_close
        self.old_on_close = None
        super().tearDown(*args, **kwargs)

    def on_window_flip(self, window):
        # Not rendering widgets in tests so don't do screenshots
        pass

    def on_motion(self, _, etype, event):
        self.etype = etype
        self.motion_event = event

    def on_any_touch_event(self, _, touch):
        self.touch_event = touch

    def assert_event(self, etype, spos):
        assert self.etype == etype
        assert 'pos' in self.motion_event.profile
        assert self.motion_event.is_touch is False
        assert self.motion_event.spos == spos

    def assert_no_event(self):
        assert self.etype is None
        assert self.motion_event is None

    def get_providers(self, with_window_children=False):
        from kivy.base import EventLoop
        win = EventLoop.window
        if with_window_children:
            from kivy.uix.button import Button
            button = Button(on_touch_down=self.on_any_touch_event,
                            on_touch_move=self.on_any_touch_event,
                            on_touch_up=self.on_any_touch_event)
            self.button_widget = button
            win.add_widget(button)
        return win, self.mouse

    def test_no_event_on_cursor_leave(self):
        win, mouse = self.get_providers()
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)
        self.assert_no_event()

    def test_no_event_on_system_size(self):
        win, mouse = self.get_providers()
        w, h = win.system_size
        win.system_size = (w + 10, h + 10)
        self.advance_frames(1)
        self.assert_no_event()

    def test_no_event_on_rotate(self):
        win, mouse = self.get_providers()
        win.rotation = 90
        self.advance_frames(1)
        self.assert_no_event()

    def test_no_event_on_close(self):
        win, mouse = self.get_providers()
        win.dispatch('on_close')
        self.advance_frames(1)
        self.assert_no_event()

    def test_begin_event_on_cursor_enter(self):
        win, mouse = self.get_providers()
        x, y = win.mouse_pos
        win.dispatch('on_cursor_enter')
        self.advance_frames(1)
        self.assert_event('begin', win.to_normalized_pos(x, y))
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_begin_event_on_mouse_pos(self):
        win, mouse = self.get_providers()
        x, y = win.mouse_pos = (10.0, 10.0)
        self.advance_frames(1)
        self.assert_event('begin', win.to_normalized_pos(x, y))
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_update_event_with_enter_and_mouse_pos(self):
        win, mouse = self.get_providers()
        win.dispatch('on_cursor_enter')
        x, y = win.mouse_pos = (50.0, 50.0)
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_update_event_with_mouse_pos(self):
        win, mouse = self.get_providers()
        win.mouse_pos = (10.0, 10.0)
        x, y = win.mouse_pos = (50.0, 50.0)
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_update_event_on_rotate(self):
        win, mouse = self.get_providers()
        x, y = win.mouse_pos = (10.0, 10.0)
        win.rotation = 90
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_update_event_on_system_size(self):
        win, mouse = self.get_providers()
        x, y = win.mouse_pos = (10.0, 10.0)
        w, h = win.system_size
        win.system_size = (w + 10, h + 10)
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_end_event_on_cursor_leave(self):
        win, mouse = self.get_providers()
        x, y = win.mouse_pos = (10.0, 10.0)
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)
        self.assert_event('end', win.to_normalized_pos(x, y))

    def test_end_event_on_window_close(self):
        win, mouse = self.get_providers()
        x, y = win.mouse_pos = (10.0, 10.0)
        win.dispatch('on_close')
        self.advance_frames(1)
        self.assert_event('end', win.to_normalized_pos(x, y))

    def test_with_full_cycle_with_cursor_events(self):
        win, mouse = self.get_providers()
        # Test begin event
        win.dispatch('on_cursor_enter')
        x, y = win.mouse_pos
        self.advance_frames(1)
        self.assert_event('begin', win.to_normalized_pos(x, y))
        # Test update event
        x, y = win.mouse_pos = (10.0, 10.0)
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        # Test end event
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)
        self.assert_event('end', win.to_normalized_pos(x, y))

    def test_with_full_cycle_with_mouse_pos_and_on_close_event(self):
        win, mouse = self.get_providers()
        # Test begin event
        x, y = win.mouse_pos = (5.0, 5.0)
        self.advance_frames(1)
        self.assert_event('begin', win.to_normalized_pos(x, y))
        # Test update event
        x, y = win.mouse_pos = (10.0, 10.0)
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        # Test end event
        win.dispatch('on_close')
        self.advance_frames(1)
        self.assert_event('end', win.to_normalized_pos(x, y))

    def test_begin_event_no_dispatch_through_on_touch_events(self):
        win, mouse = self.get_providers(with_window_children=True)
        x, y = win.mouse_pos
        win.dispatch('on_cursor_enter')
        self.advance_frames(1)
        self.assert_event('begin', win.to_normalized_pos(x, y))
        assert self.touch_event is None
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_update_event_no_dispatch_through_on_touch_events(self):
        win, mouse = self.get_providers(with_window_children=True)
        win.dispatch('on_cursor_enter')
        x, y = win.mouse_pos = (10.0, 10.0)
        self.advance_frames(1)
        self.assert_event('update', win.to_normalized_pos(x, y))
        assert self.touch_event is None
        # Cleanup
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)

    def test_end_event_no_dispatch_through_on_touch_events(self):
        win, mouse = self.get_providers(with_window_children=True)
        win.dispatch('on_cursor_enter')
        x, y = win.mouse_pos = (10.0, 10.0)
        win.dispatch('on_cursor_leave')
        self.advance_frames(1)
        self.assert_event('end', win.to_normalized_pos(x, y))
        assert self.touch_event is None

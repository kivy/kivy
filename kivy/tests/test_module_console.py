from kivy.tests.common import GraphicUnitTest, UnitTestTouch


def clock_events_of(*objs):
    # repeating callbacks of these objects that are still scheduled
    from kivy.clock import Clock
    return [
        ev for ev in Clock.get_events()
        if ev.loop and any(getattr(ev.get_callback(), '__self__', None) is obj
               for obj in objs)]


class ConsoleModuleTestCase(GraphicUnitTest):

    def setUp(self):
        super().setUp()
        from kivy.base import EventLoop
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        EventLoop.ensure_window()
        self.win = EventLoop.window
        for child in self.win.children[:]:
            self.win.remove_widget(child)
        self.root = BoxLayout()
        self.button = Button(text='target')
        self.root.add_widget(self.button)
        self.render(self.root)

    def tearDown(self, *args, **kwargs):
        from kivy.modules import console
        console.stop(self.win, self.root)
        super().tearDown(*args, **kwargs)

    def start_console(self):
        from kivy.modules import console
        console.start(self.win, self.root)
        self.advance_frames(2)
        return self.root.console

    def ctrl_e(self, modifiers=('ctrl', )):
        self.win.dispatch('on_keyboard', 101, 0, 'e', list(modifiers))

    def test_stop_before_create(self):
        from kivy.modules import console
        console.start(self.win, self.root)
        console.stop(self.win, self.root)
        self.advance_frames(2)

        self.assertFalse(hasattr(self.root, 'console'))
        self.ctrl_e()
        self.assertEqual(
            [c for c in self.win.children
             if isinstance(c, console.Console)], [])

    def test_deactivate_removes_from_window(self):
        con = self.start_console()
        self.assertNotIn(con, self.win.children)

        con.activated = True
        self.assertIs(self.win.children[0], con)
        con.activated = False
        self.assertNotIn(con, self.win.children)
        self.assertEqual(self.win.canvas.children.count(con.canvas), 0)

        con.activated = True
        self.assertIs(self.win.children[0], con)
        self.assertEqual(self.win.children.count(con), 1)
        self.assertEqual(self.win.canvas.children.count(con.canvas), 1)
        self.assertEqual(con.y, 0)

    def test_select_after_reactivation(self):
        con = self.start_console()
        con.activated = True
        self.advance_frames(1)
        con.activated = False
        self.advance_frames(1)
        con.activated = True
        self.advance_frames(1)

        # the Select addon and on_touch_down still pick widgets
        con.inspect_enabled = True
        touch = UnitTestTouch(*self.button.center)
        touch.touch_down()
        touch.touch_up()
        self.assertIs(con.widget, self.button)

        # the Properties panel is bound to the selection again
        content = con.ids.content
        self.assertEqual(len(content.children), 1)

    def test_no_clock_events_while_deactivated(self):
        con = self.start_console()
        self.assertEqual(clock_events_of(con, *con._addons), [])

        con.activated = True
        self.advance_frames(1)
        self.assertTrue(clock_events_of(con, *con._addons))

        # includes the Fps addon's update
        con.activated = False
        self.assertEqual(clock_events_of(con, *con._addons), [])

    def test_stop_while_activated(self):
        from kivy.modules import console
        con = self.start_console()
        con.activated = True
        self.advance_frames(1)

        console.stop(self.win, self.root)
        self.assertFalse(con.activated)
        self.assertNotIn(con, self.win.children)
        self.assertEqual(clock_events_of(con, *con._addons), [])

    def test_activation_adds_itself_once(self):
        con = self.start_console()
        dispatches = []
        uid = self.win.fbind('children', lambda *args: dispatches.append(1))
        try:
            con.activated = True
        finally:
            self.win.unbind_uid('children', uid)

        self.assertEqual(len(dispatches), 1)
        self.assertIs(self.win.children[0], con)
        self.assertEqual(self.win.canvas.children.count(con.canvas), 1)

    def test_ctrl_e_with_numlock(self):
        con = self.start_console()
        self.ctrl_e(('ctrl', 'numlock'))
        self.assertTrue(con.activated)
        self.ctrl_e(('ctrl', 'shift'))
        self.assertTrue(con.activated)
        self.ctrl_e()
        self.assertFalse(con.activated)

    def test_with_inspector_stays_on_top(self):
        from kivy.modules import inspector
        from kivy.uix.widget import Widget
        con = self.start_console()
        inspector.start(self.win, self.root)
        self.advance_frames(2)
        ins = self.root.inspector
        try:
            con.activated = True
            ins.activated = True
            self.assertEqual(set(self.win.children[:2]), {con, ins})

            # nothing to do while both are already above the others
            dispatches = []
            uid = self.win.fbind(
                'children', lambda *args: dispatches.append(1))
            try:
                ins.on_window_children(self.win, self.win.children)
                con.on_window_children(self.win, self.win.children)
            finally:
                self.win.unbind_uid('children', uid)
            self.assertEqual(dispatches, [])

            widget = Widget()
            uid = self.win.fbind(
                'children', lambda *args: dispatches.append(1))
            try:
                self.win.add_widget(widget)
            finally:
                self.win.unbind_uid('children', uid)
            # was 13 when each observer re-added itself unconditionally
            self.assertLessEqual(len(dispatches), 5)
            self.assertEqual(set(self.win.children[:2]), {con, ins})
            self.assertIs(self.win.children[2], widget)
            for w in (con, ins, widget):
                self.assertEqual(self.win.children.count(w), 1)
                self.assertEqual(
                    self.win.canvas.children.count(w.canvas), 1)

            # an unrelated removal doesn't make them swap places
            order = self.win.children[:2]
            del dispatches[:]
            uid = self.win.fbind(
                'children', lambda *args: dispatches.append(1))
            try:
                self.win.remove_widget(widget)
            finally:
                self.win.unbind_uid('children', uid)
            self.assertEqual(len(dispatches), 1)
            self.assertEqual(self.win.children[:2], order)
        finally:
            inspector.stop(self.win, self.root)

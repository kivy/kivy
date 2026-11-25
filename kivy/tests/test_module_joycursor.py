from kivy.tests.common import GraphicUnitTest


def clock_events_of(obj):
    # repeating callbacks of obj that are still scheduled
    from kivy.clock import Clock
    return [
        ev for ev in Clock.get_events()
        if ev.loop and getattr(ev.get_callback(), '__self__', None) is obj]


class JoyCursorModuleTestCase(GraphicUnitTest):

    def setUp(self):
        super().setUp()
        from kivy.base import EventLoop
        from kivy.uix.widget import Widget
        EventLoop.ensure_window()
        self.win = EventLoop.window
        for child in self.win.children[:]:
            self.win.remove_widget(child)
        self.root = Widget()
        self.render(self.root)

    def tearDown(self, *args, **kwargs):
        from kivy.modules import joycursor
        joycursor.stop(self.win, self.root)
        super().tearDown(*args, **kwargs)

    def start_joycursor(self):
        from kivy.modules import joycursor
        joycursor.start(self.win, self.root)
        self.advance_frames(2)
        return self.root.joycursor

    def ctrl_e(self, modifiers=('ctrl', )):
        self.win.dispatch('on_keyboard', 101, 0, 'e', list(modifiers))

    def test_stop_before_create(self):
        from kivy.modules import joycursor
        joycursor.start(self.win, self.root)
        joycursor.stop(self.win, self.root)
        self.advance_frames(2)

        self.assertFalse(hasattr(self.root, 'joycursor'))
        self.ctrl_e()
        self.assertEqual(
            [c for c in self.win.children
             if isinstance(c, joycursor.JoyCursor)], [])

    def test_activate_deactivate(self):
        jc = self.start_joycursor()
        dispatches = []
        uid = self.win.fbind('children', lambda *args: dispatches.append(1))
        try:
            jc.activated = True
        finally:
            self.win.unbind_uid('children', uid)

        # no remove/re-add from its own children observer
        self.assertEqual(len(dispatches), 1)
        self.assertIs(self.win.children[0], jc)
        self.assertEqual(self.win.canvas.children.count(jc.canvas), 1)
        self.assertTrue(clock_events_of(jc))

        jc.activated = False
        self.assertNotIn(jc, self.win.children)
        self.assertEqual(clock_events_of(jc), [])

    def test_stays_on_top(self):
        from kivy.uix.widget import Widget
        jc = self.start_joycursor()
        jc.activated = True
        widget = Widget()
        self.win.add_widget(widget)
        self.assertIs(self.win.children[0], jc)
        self.assertIs(self.win.children[1], widget)
        self.assertEqual(self.win.canvas.children.count(jc.canvas), 1)
        self.win.remove_widget(widget)

    def test_ctrl_e_with_numlock(self):
        jc = self.start_joycursor()
        self.ctrl_e(('ctrl', 'numlock'))
        self.assertTrue(jc.activated)
        self.ctrl_e(('ctrl', 'shift'))
        self.assertTrue(jc.activated)
        self.ctrl_e()
        self.assertFalse(jc.activated)

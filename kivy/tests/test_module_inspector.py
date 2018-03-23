from kivy.tests.common import GraphicUnitTest, UnitTestTouch

from kivy.base import EventLoop
from kivy.modules import inspector
from kivy.factory import Factory


KV = '''
#:import Factory kivy.factory.Factory

<InspectorTestModal@ModalView>:
    size_hint: 0.5, 0.5

<FirstModal@InspectorTestModal>:
    Button:
        id: firstmodal
        text: 'first modal'
        on_release: Factory.SecondModal().open()

<SecondModal@InspectorTestModal>:
    Button:
        id: secondmodal
        text: 'second modal'
        on_release: Factory.ThirdModal().open()

<ThirdModal@InspectorTestModal>:
    Button:
        id: thirdmodal
        text: 'third modal'

BoxLayout:
    Button:
        id: highlight
        text: 'highlight'
    Button:
        id: popup
        text: 'popup'
        on_release: Factory.FirstModal().open()
    Button:
        id: tri_popup
        text: '3 popups'
        on_release: Factory.FirstModal().open()
    Button:
        id: dummy
        text: 'dummy'
'''


class InspectorTestCase(GraphicUnitTest):
    framecount = 0

    def setUp(self):
        # kill KV lang logging (too long test)
        import kivy.lang.builder as builder

        if not hasattr(self, '_trace'):
            self._trace = builder.trace

        self.builder = builder
        builder.trace = lambda *_, **__: None
        super(InspectorTestCase, self).setUp()

    def tearDown(self):
        # add the logging back
        import kivy.lang.builder as builder
        builder.Builder.unload_file("InspectorTestCase.KV")
        builder.trace = self._trace
        super(InspectorTestCase, self).tearDown()

    def clean_garbage(self, *args):
        for child in self._win.children[:]:
            self._win.remove_widget(child)
        self.advance_frames(5)

    def test_activate_deactivate_bottom(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.clean_garbage()

        # build the widget tree & add Window as the main EL
        self.root = self.builder.Builder.load_string(
            KV, filename="InspectorTestCase.KV")
        self.render(self.root)
        self.assertLess(len(self._win.children), 2)

        # activate inspector with root as ctx
        inspector.start(self._win, self.root)
        self.advance_frames(2)

        # pull the Inspector drawer from bottom
        ins = self.root.inspector
        ins.activated = True
        ins.inspect_enabled = True
        self.assertTrue(ins.at_bottom)

        # by default is Inspector appended as the first child
        # to the window and positioned at the bottom
        self.assertEqual(self._win.children[0], ins)
        self.advance_frames(1)
        self.assertLess(ins.layout.pos[1], self._win.height / 2.0)

        # close Inspector
        ins.inspect_enabled = False
        ins.activated = False
        self.render(self.root)
        self.advance_frames(1)

        # stop Inspector completely
        inspector.stop(self._win, self.root)
        self.assertLess(len(self._win.children), 2)
        self.render(self.root)

    def test_activate_deactivate_top(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.clean_garbage()

        # build the widget tree & add Window as the main EL
        self.root = self.builder.Builder.load_string(
            KV, filename="InspectorTestCase.KV")
        self.render(self.root)
        self.assertLess(len(self._win.children), 2)

        # activate inspector with root as ctx
        inspector.start(self._win, self.root)
        self.advance_frames(2)

        # pull the Inspector drawer from top
        ins = self.root.inspector
        ins.at_bottom = False
        ins.activated = True
        ins.inspect_enabled = True
        self.assertFalse(ins.at_bottom)

        # by default is Inspector appended as the first child
        # to the window & we move it to the top
        self.assertEqual(self._win.children[0], ins)
        ins.toggle_position(self.root.ids.dummy)
        self.advance_frames(20)  # drawer is moving, like with activate
        self.assertGreater(ins.layout.pos[1], self._win.height / 2.0)

        # close Inspector
        ins.inspect_enabled = False
        ins.activated = False
        self.render(self.root)
        self.advance_frames(1)

        # stop Inspector completely
        inspector.stop(self._win, self.root)
        self.assertLess(len(self._win.children), 2)
        self.render(self.root)

    def test_widget_button(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.clean_garbage()

        # build the widget tree & add Window as the main EL
        self.root = self.builder.Builder.load_string(
            KV, filename="InspectorTestCase.KV")
        self.render(self.root)
        self.assertLess(len(self._win.children), 2)

        # checked widget
        highlight = self.root.ids.highlight
        highlight_exp = self.root.ids.highlight.text

        # activate inspector with root as ctx
        inspector.start(self._win, self.root)
        self.advance_frames(2)

        # pull the Inspector drawer from bottom
        ins = self.root.inspector
        ins.activated = True
        ins.inspect_enabled = True
        self.assertTrue(ins.at_bottom)

        # touch button center
        touch = UnitTestTouch(*highlight.center)
        touch.touch_down()
        touch.touch_up()

        # open Inspector properties
        ins.show_widget_info()
        self.advance_frames(2)

        # check if the button is selected
        # stored instance
        self.assertEqual(ins.widget.text, highlight_exp)
        # data in properties
        for node in ins.treeview.iterate_all_nodes():
            lkey = getattr(node.ids, 'lkey', None)
            if not lkey:
                continue
            if lkey.text == 'text':
                ltext = node.ids.ltext
                # slice because the string is displayed with quotes
                self.assertEqual(ltext.text[1:-1], highlight_exp)
                break

        # close Inspector
        ins.inspect_enabled = False
        ins.activated = False
        self.render(self.root)
        self.advance_frames(1)

        # stop Inspector completely
        inspector.stop(self._win, self.root)
        self.assertLess(len(self._win.children), 2)
        self.render(self.root)

    def test_widget_popup(self, *args):
        from kivy.logger import Logger
        Logger.info('test_momdule_popup.py: 1. Entering')
        EventLoop.ensure_window()
        self._win = EventLoop.window

        Logger.info('test_momdule_popup.py: 2. Clean garbage')
        self.clean_garbage()

        # build the widget tree & add Window as the main EL
        Logger.info('test_momdule_popup.py: 3. Set root')
        self.root = self.builder.Builder.load_string(
            KV, filename="InspectorTestCase.KV")
        Logger.info('test_momdule_popup.py: 4. Render')
        self.render(self.root)
        Logger.info('test_momdule_popup.py: 5. Assert')
        self.assertLess(len(self._win.children), 2)

        # checked widget
        Logger.info('test_momdule_popup.py: 6. Popup')
        popup = self.root.ids.popup
        Logger.info('test_momdule_popup.py: 7. Popup_exp')
        popup_exp = self.root.ids.popup.text

        Logger.info('test_momdule_popup.py: 8. Popup')
        # activate inspector with root as ctx
        inspector.start(self._win, self.root)
        Logger.info('test_momdule_popup.py: 9. Advance')
        self.advance_frames(1)

        # pull the Inspector drawer from bottom,
        # but don't inspect yet!
        Logger.info('test_momdule_popup.py: 10. ins')
        ins = self.root.inspector
        Logger.info('test_momdule_popup.py: 11. Disable')
        ins.inspect_enabled = False
        Logger.info('test_momdule_popup.py: 12. Activate')
        ins.activated = True
        Logger.info('test_momdule_popup.py: 13. Assert')
        self.assertTrue(ins.at_bottom)

        # touch button center to open the popup
        Logger.info('test_momdule_popup.py: 14. UnitTouch')
        touch = UnitTestTouch(*popup.center)
        Logger.info('test_momdule_popup.py: 15. Down')
        touch.touch_down()
        Logger.info('test_momdule_popup.py: 16. Up')
        touch.touch_up()
        Logger.info('test_momdule_popup.py: 17. Advance')
        self.advance_frames(1)

        # start inspecting
        Logger.info('test_momdule_popup.py: 18. Enabled')
        ins.inspect_enabled = True
        Logger.info('test_momdule_popup.py: 19. Advance')
        self.advance_frames(1)

        # inspect FirstModal's button
        Logger.info('test_momdule_popup.py: 20. Down')
        touch.touch_down()
        Logger.info('test_momdule_popup.py: 21. UP')
        touch.touch_up()
        Logger.info('test_momdule_popup.py: 22. Advance')
        self.advance_frames(1)

        # open Inspector properties
        Logger.info('test_momdule_popup.py: 23. Info')
        ins.show_widget_info()
        Logger.info('test_momdule_popup.py: 24. Advance')
        self.advance_frames(2)

        # check if the popup is selected
        # stored instance
        Logger.info('test_momdule_popup.py: 25. Asserts')
        self.assertIsInstance(ins.widget, Factory.Button)
        self.assertIsInstance(ins.widget.parent, Factory.FirstModal)
        # check with new Popup instance if the properties match
        Logger.info('test_momdule_popup.py: 26. Popup')
        temp_popup = Factory.FirstModal()
        Logger.info('test_momdule_popup.py: 27. Popup_exp')
        temp_popup_exp = temp_popup.ids.firstmodal.text
        Logger.info('test_momdule_popup.py: 28. Assert')
        self.assertEqual(ins.widget.text, temp_popup_exp)
        # data in properties
        Logger.info('test_momdule_popup.py: 29. Loop')
        for node in ins.treeview.iterate_all_nodes():
            lkey = getattr(node.ids, 'lkey', None)
            if not lkey:
                continue
            if lkey.text == 'text':
                ltext = node.ids.ltext
                # slice because the string is displayed with quotes
                self.assertEqual(ltext.text[1:-1], temp_popup_exp)
                break
        del temp_popup

        # close popup
        Logger.info('test_momdule_popup.py: 30. Dsisable')
        ins.inspect_enabled = False
        Logger.info('test_momdule_popup.py: 31. UnitTOuch')
        touch = UnitTestTouch(0, 0)
        Logger.info('test_momdule_popup.py: 32. Down')
        touch.touch_down()
        Logger.info('test_momdule_popup.py: 33. Up')
        touch.touch_up()
        Logger.info('test_momdule_popup.py: 34. Advance')
        self.advance_frames(10)

        # close Inspector
        Logger.info('test_momdule_popup.py: 35. deactivate')
        ins.activated = False
        Logger.info('test_momdule_popup.py: 36. render')
        self.render(self.root)
        Logger.info('test_momdule_popup.py: 37. advance')
        self.advance_frames(10)

        # stop Inspector completely
        Logger.info('test_momdule_popup.py: 38. stop')
        inspector.stop(self._win, self.root)
        Logger.info('test_momdule_popup.py: 39. Assert')
        self.assertLess(len(self._win.children), 2)
        Logger.info('test_momdule_popup.py: 40. Render')
        self.render(self.root)
        Logger.info('test_momdule_popup.py: 41. exit')

    def test_widget_multipopup(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.clean_garbage()

        # build the widget tree & add Window as the main EL
        self.root = self.builder.Builder.load_string(
            KV, filename="InspectorTestCase.KV")
        self.render(self.root)
        self.assertLess(len(self._win.children), 2)

        # checked widget
        popup = self.root.ids.popup
        popup_exp = self.root.ids.popup.text

        # activate inspector with root as ctx
        inspector.start(self._win, self.root)
        self.advance_frames(1)

        # pull the Inspector drawer from bottom,
        # but don't inspect yet!
        ins = self.root.inspector
        ins.inspect_enabled = False
        ins.activated = True
        self.assertTrue(ins.at_bottom)

        # touch button center to open the popup
        touch = UnitTestTouch(*popup.center)
        touch.touch_down()
        touch.touch_up()
        self.advance_frames(1)

        # touch Window center to open
        # the second and the third popup
        touch = UnitTestTouch(
            self._win.width / 2.0,
            self._win.height / 2.0
        )
        for i in range(2):
            touch.touch_down()
            touch.touch_up()
            self.advance_frames(1)

        # fixed order, first opened - last closed
        modals = (
            Factory.ThirdModal,
            Factory.SecondModal,
            Factory.FirstModal
        )
        for mod in modals:
            # start inspecting
            ins.inspect_enabled = True
            self.advance_frames(1)

            # inspect button
            touch.touch_down()
            touch.touch_up()
            self.advance_frames(1)

            # check if the popup is selected
            # stored instance
            self.assertIsInstance(ins.widget, Factory.Button)
            self.assertIsInstance(ins.widget.parent, mod)

            # close popup
            ins.inspect_enabled = False
            orig = UnitTestTouch(0, 0)
            orig.touch_down()
            orig.touch_up()
            self.advance_frames(10)

        # close Inspector
        ins.activated = False
        self.render(self.root)
        self.advance_frames(10)

        # stop Inspector completely
        inspector.stop(self._win, self.root)
        self.assertLess(len(self._win.children), 2)
        self.render(self.root)


if __name__ == '__main__':
    import unittest
    unittest.main()

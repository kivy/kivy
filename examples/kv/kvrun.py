#!/usr/bin/env python
'''
Run KV Applications Demo
========================

This runs applications in kv files specified on the command line. For example,
if you run 'python kvrun.py app_scatter.kv' you should see a 'kiwi
crossing' sign in the lower right corner. The console output will show the
fps (average frames per second) and rfps ('real' fps calculated by clock).
Hitting the F5 key will cause the .kv file to reload.

There are different possible kv files, some of which are more finished
than others.
'''
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window, Keyboard

F5 = Keyboard.keycodes['f5']


class KvApp(App):
    def _print_fps(self, *largs):
        print('FPS: %2.4f (real draw: %d)' % (
            Clock.get_fps(), Clock.get_rfps()))

    def _reload_keypress(self, instance, code, *largs):
        ''' reload if f5 pressed '''
        if code != F5:
            return
        print('reloading...')
        for child in Window.children[:]:
            Window.remove_widget(child)
        root = Builder.load_file(self.options['filename'])
        Window.add_widget(root)

    def build(self):
        Clock.schedule_interval(self._print_fps, 1)
        Window.bind(on_keyboard=self._reload_keypress)
        return Builder.load_file(self.options['filename'])

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 2:
        print('Usage: %s filename.kv' % os.path.basename(sys.argv[0]))
        sys.exit(1)

    KvApp(filename=sys.argv[1]).run()

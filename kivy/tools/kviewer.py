#!/usr/bin/env python
'''
KViewer
=======

KViewer, for KV-Viewer, is a simple tool allowing you to dynamically display
a KV file, taking its changes into account (thanks to watchdog). The
idea is to facilitate design using the KV language. It's somewhat related to
the KivyCatalog demo, except it uses an on-disc file, allowing the user to use
any editor.

You can use the script as follows::

    python kviewer.py ./test.kv

This will display the test.kv and automatically update the display when the
file changes.

.. note: This scripts uses watchdog to listen for file changes. To install
   watchdog::

   pip install watchdog

'''

from sys import argv
from kivy.lang import Builder
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.uix.label import Label

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from os.path import dirname, basename, join


if len(argv) != 2:
    print('usage: %s filename.kv' % argv[0])
    exit(1)


PATH = dirname(argv[1])
TARGET = basename(argv[1])


class KvHandler(FileSystemEventHandler):
    def __init__(self, callback, target, **kwargs):
        super(KvHandler, self).__init__(**kwargs)
        self.callback = callback
        self.target = target

    def on_any_event(self, event):
        if basename(event.src_path) == self.target:
            self.callback()


class KvViewerApp(App):
    def build(self):
        o = Observer()
        o.schedule(KvHandler(self.update, TARGET), PATH)
        o.start()
        Clock.schedule_once(self.update, 1)
        return super(KvViewerApp, self).build()

    @mainthread
    def update(self, *args):
        Builder.unload_file(join(PATH, TARGET))
        for w in Window.children[:]:
            Window.remove_widget(w)
        try:
            Window.add_widget(Builder.load_file(join(PATH, TARGET)))
        except Exception as e:
            Window.add_widget(Label(text=(
                e.message if getattr(e, r'message', None) else str(e)
            )))


if __name__ == '__main__':
    KvViewerApp().run()

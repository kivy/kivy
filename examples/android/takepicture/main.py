'''
Take picture
============

.. author:: Mathieu Virbel <mat@kivy.org>

Little example to demonstrate how to start an Intent, and get the result.
When you use the Android.startActivityForResult(), the result will be dispatched
into onActivityResult. You can catch the event with the android.activity API
from python-for-android project.

If you want to compile it, don't forget to add the CAMERA permission::

    ./build.py --name 'TakePicture' --package org.test.takepicture \
            --permission CAMERA --version 1 \
            --private ~/code/kivy/examples/android/takepicture \
            debug installd

'''

__version__ = '0.1'

from kivy.app import App
from os.path import exists
from jnius import autoclass, cast
from android import activity
from functools import partial
from kivy.clock import Clock
from kivy.uix.scatter import Scatter
from kivy.properties import StringProperty

from PIL import Image

Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
MediaStore = autoclass('android.provider.MediaStore')
Uri = autoclass('android.net.Uri')
Environment = autoclass('android.os.Environment')


class Picture(Scatter):
    source = StringProperty(None)


class TakePictureApp(App):
    def build(self):
        self.index = 0
        activity.bind(on_activity_result=self.on_activity_result)

    def get_filename(self):
        while True:
            self.index += 1
            fn = (Environment.getExternalStorageDirectory().getPath() +
                  '/takepicture{}.jpg'.format(self.index))
            if not exists(fn):
                return fn

    def take_picture(self):
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        self.last_fn = self.get_filename()
        self.uri = Uri.parse('file://' + self.last_fn)
        self.uri = cast('android.os.Parcelable', self.uri)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, self.uri)
        PythonActivity.mActivity.startActivityForResult(intent, 0x123)

    def on_activity_result(self, requestCode, resultCode, intent):
        if requestCode == 0x123:
            Clock.schedule_once(partial(self.add_picture, self.last_fn), 0)

    def add_picture(self, fn, *args):
        im = Image.open(fn)
        width, height = im.size
        im.thumbnail((width / 4, height / 4), Image.ANTIALIAS)
        im.save(fn, quality=95)
        self.root.add_widget(Picture(source=fn, center=self.root.center))

    def on_pause(self):
        return True

TakePictureApp().run()

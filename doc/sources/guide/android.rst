.. _android:

Kivy on Android
===============

We want to thank Renpy's Tom for being able to run pygame on android,
using his `Pygame Subset for Android <http://renpy.org/pygame/>`_ project.

We made some changes to his project to be able to use it with Kivy:

- Support for multitouch events
- OpenGL ES 2.0 surface
- Include more Python modules
- Removed main() function and use __main__ approach
- Various enhancements on the build system for Kivy

Introduction to the Kivy Launcher
---------------------------------

The Kivy launcher is an application to run any Kivy examples stored on your
SD Card from android. See :ref:`androidinstall`.

Your application must be saved into::

    /sdcard/kivy/<yourapplication>

Your application directory must contain::

    # Your main application file:
    main.py
    # Some infos Kivy requires about your app on android:
    android.txt

The file `main.py` is the same as your original code. If you want to support
android, you must change the __main__ line to, though::

    if __name__ in ('__main__', '__android__'):
        YourApp().run()

The file `android.txt` must contain::

    title=<Application Title>
    author=<Your Name>
    orientation=<portrait|landscape>

Status of the Project
---------------------

Missing providers:

- Video
- Camera
- Audio (can use RenPySound)

Missing features:

- Keyboard mapping for main button
- Keyboard support in TextInput widget
- Ability to hook app on sleep/wakeup
- Ability for an application to have a settings screen

Tested Devices
--------------

These Android devices have been confirmed working with Kivy. If your
device is not on the list, that does not mean that it is not supported.
If that is the case, please try running Kivy and if it succeeds let us
know so that we can update this list. Note, however, that your device has
to support at least OpenGL 2.0 ES.

- Motorola Droid 1
- Motorola Droid 2
- Samsung Galaxy Tab
- HTC Desire
- HTC Desire Z
- Xperia 10 (custom ROM 2.1 + GLES 2.0 support)


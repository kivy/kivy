Android platform
================

We want to thanks Renpy Tom for beeing able to run pygame on android,
with his `Pygame Subset for Android <http://renpy.org/pygame/>`_ project.

The changes made from his project are :

- Support of multitouch event
- OpenGL ES 2.0 surface
- Include more Python modules
- Removing main() function and use __main__ hack.
- Various enhancements on the build system for Kivy

Introduction to the Kivy Launcher
---------------------------------

The Kivy launcher is an application to run any kivy examples stored on your
sdcard from android. Check the :doc:`installation-android`.

Your application must be saved into::

    /sdcard/kivy/<yourapplication>

Your application directory must contain::

    main.py # <-- Your main application file
    android.txt # <-- Some indication for running your application

The `main.py` is the same as your original code. If you want to support android,
you must change the __main__ line to::

    if __name__ in ('__main__', '__android__'):
        YourApp().run()

The `android.txt` can contain::

    title=<Application Title>
    author=<Your Name>
    orientation=<portrait|landscape>

Status of the project
---------------------

Missing providers:

- Video
- Camera
- Audio (can use RenPySound)

Missing features:

- Keyboard mapping for main button
- Keyboard support in future TextInput widget
- Ability to hook app on sleep/wakeup
- Ability for an application to have a settings screen

Working devices
---------------

- Motorola Droid 1
- Motorola Droid 2
- Samsung Galaxy Tab
- HTC Desire
- HTC Desire Z
- Xperia 10 (custom ROM 2.1 + GLES 2.0 support)


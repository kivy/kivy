.. _environment:

Controling the environment
==========================

Many environment variables are available to control the initialization and
behavior of Kivy.

For example, for restricting text rendering to PIL implementation::

    $ KIVY_TEXT=pil python main.py

Environment variable can be set before importing kivy::

    import os
    os.environ['KIVY_TEXT'] = 'pil'
    import kivy

Configuration
-------------

KIVY_USE_DEFAULTCONFIG
    If this name is found in environ, Kivy will not read the user config file.

Path control
------------

.. versionadded:: 1.0.7

You can control where is located default directory of modules, extensions, and
kivy datas.

KIVY_DATA_DIR
    Location of the Kivy data, default to `<kivy path>/data`

KIVY_EXTS_DIR
    Location of the Kivy extensions, default to `<kivy path>/extensions`

KIVY_MODULES_DIR
    Location of the Kivy modules, default to `<kivy path>/modules`

Restrict core to specific implementation
----------------------------------------

:mod:`kivy.core` try to select the best implementation available for your
platform. For testing or custom installation, you might want to restrict the
selector to a specific implementation.

KIVY_WINDOW
    Implementation to use for creating the Window

    Values: pygame

KIVY_TEXT
    Implementation to use for rendering text

    Values: pil, pygame

KIVY_VIDEO
    Implementation to use for rendering video

    Values: gstreamer, pyglet, ffmpeg

KIVY_AUDIO
    Implementation to use for playing audio

    Values: gstreamer, pygame

KIVY_IMAGE
    Implementation to use for reading image

    Values: pil, pygame

KIVY_CAMERA
    Implementation to use for reading camera

    Values: gstreamer, opencv, videocapture

KIVY_SPELLING
    Implementation to use for spelling

    Values: enchant, osxappkit

KIVY_CLIPBOARD
    Implementation to use for clipboard management

    Values: pygame, dummy

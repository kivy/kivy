.. _environment:

Controlling the environment
===========================

Many environment variables are available to control the initialization and
behavior of Kivy.

For example, in order to restrict text rendering to the PIL implementation::

    $ KIVY_TEXT=pil python main.py

Environment variables should be set before importing kivy::

    import os
    os.environ['KIVY_TEXT'] = 'pil'
    import kivy

Path control
------------

.. versionadded:: 1.0.7

You can control the default directories where config files, modules,
extensions, and kivy data are located.

KIVY_DATA_DIR
    Location of the Kivy data, defaults to `<kivy path>/data`

KIVY_EXTS_DIR
    Location of the Kivy extensions, defaults to `<kivy path>/extensions`

KIVY_MODULES_DIR
    Location of the Kivy modules, defaults to `<kivy path>/modules`

KIVY_HOME
    Location of the Kivy home. This directory is used for local configuration,
    and must be in a writable location.

    Defaults to:
     - Desktop: `<user home>/.kivy`
     - Android: `<android app path>/.kivy`
     - iOS: `<user home>/Documents/.kivy`

    .. versionadded:: 1.9.0

KIVY_SDL2_PATH
    If set, the SDL2 libraries and headers from this path are used when
    compiling kivy instead of the ones installed system-wide.
    To use the same libraries while running a kivy app, this path must be
    added at the start of the PATH environment variable.

    .. versionadded:: 1.9.0

    .. warning::

        This path is required for the compilation of Kivy. It is not
        required for program execution.


Configuration
-------------

KIVY_USE_DEFAULTCONFIG
    If this name is found in environ, Kivy will not read the user config file.

KIVY_NO_CONFIG
    If set, no configuration file will be read or written to. This also applies
    to the user configuration directory.

KIVY_NO_FILELOG
    If set, logs will be not print to a file

KIVY_NO_CONSOLELOG
    If set, logs will be not print to the console

KIVY_NO_ARGS
    If set, the argument passed in command line will not be parsed and used by Kivy.
    Ie, you can safely make a script or an app with your own arguments without
    requiring the `--` delimiter::

        import os
        os.environ["KIVY_NO_ARGS"] = "1"
        import kivy

    .. versionadded:: 1.9.0

Restrict core to specific implementation
----------------------------------------

:mod:`kivy.core` try to select the best implementation available for your
platform. For testing or custom installation, you might want to restrict the
selector to a specific implementation.

KIVY_WINDOW
    Implementation to use for creating the Window

    Values: sdl2, pygame, x11, egl_rpi

KIVY_TEXT
    Implementation to use for rendering text

    Values: sdl2, pil, pygame, sdlttf

KIVY_VIDEO
    Implementation to use for rendering video

    Values: pygst, gstplayer, pyglet, ffpyplayer, ffmpeg, gi, null

KIVY_AUDIO
    Implementation to use for playing audio

    Values: sdl2, gstplayer, pygst, ffpyplayer, pygame, gi, avplayer

KIVY_IMAGE
    Implementation to use for reading image

    Values: sdl2, pil, pygame, imageio, tex, dds, gif

KIVY_CAMERA
    Implementation to use for reading camera

    Values: videocapture, avfoundation, pygst, opencv

KIVY_SPELLING
    Implementation to use for spelling

    Values: enchant, osxappkit

KIVY_CLIPBOARD
    Implementation to use for clipboard management

    Values: sdl2, pygame, dummy, android

Metrics
-------

KIVY_DPI
    If set, the value will be used for :attr:`Metrics.dpi`.

    .. versionadded:: 1.4.0

KIVY_METRICS_DENSITY
    If set, the value will be used for :attr:`Metrics.density`.

    .. versionadded:: 1.5.0

KIVY_METRICS_FONTSCALE

    If set, the value will be used for :attr:`Metrics.fontscale`.

    .. versionadded:: 1.5.0

Graphics
--------

KIVY_GLES_LIMITS
    Whether the GLES2 restrictions are enforced (the default, or if set to
    1). If set to false, Kivy will not be truly GLES2 compatible.

    Following is a list of the potential incompatibilities that result
    when set to true.

==============	====================================================
Mesh indices	If true, the number of indices in a mesh is limited
                to 65535
Texture blit    When blitting to a texture, the data (color and
                buffer) format must be the same format as the one
                used at the texture creation. On desktop, the
                conversion of different color is correctly handled
                by the driver, while on Android, most of devices
                fail to do it.
                Ref: https://github.com/kivy/kivy/issues/1600
==============	====================================================

    .. versionadded:: 1.8.1

KIVY_BCM_DISPMANX_ID
    Change the default Raspberry Pi display to use. The list of available value
    is accessible in `vc_dispmanx_types.h`. Default value is 0:

    - 0: DISPMANX_ID_MAIN_LCD
    - 1: DISPMANX_ID_AUX_LCD
    - 2: DISPMANX_ID_HDMI
    - 3: DISPMANX_ID_SDTV
    - 4: DISPMANX_ID_FORCE_LCD
    - 5: DISPMANX_ID_FORCE_TV
    - 6: DISPMANX_ID_FORCE_OTHER

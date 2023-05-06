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

You can control the default directories where config files, modules
and kivy data are located.

KIVY_DATA_DIR
    Location of the Kivy data, defaults to `<kivy path>/data`

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

KIVY_SDL2_FRAMEWORKS_SEARCH_PATH
    If set, the SDL2 frameworks from this path are used when compiling kivy
    instead of the ones installed system-wide.

    That path is used only on macOS, and must contain the SDL2.framework,
    SDL_image.framework, SDL_mixer.framework and SDL_ttf.framework.

    .. versionadded:: 2.1.0

    .. warning::

        This path is required for the compilation of Kivy. It is not
        required for program execution.

KIVY_DEPS_ROOT
    If set, during build, Kivy will use this directory as the root one to
    search for (only SDL ATM) dependencies. Please note that if `KIVY_SDL2_PATH` or
    `KIVY_SDL2_FRAMEWORKS_SEARCH_PATH` are set, they will be used instead.

    .. versionadded:: 2.2.0

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
    If set to one of ('true', '1', 'yes'), the argument passed in command line
    will not be parsed and used by Kivy. Ie, you can safely make a script or an
    app with your own arguments without requiring the `--` delimiter::

        import os
        os.environ["KIVY_NO_ARGS"] = "1"
        import kivy

    .. versionadded:: 1.9.0

KCFG_section_key
    If a such format environment name is detected, it will be mapped
    to the Config object. They are loaded only once when `kivy` is
    imported. The behavior can be disabled using `KIVY_NO_ENV_CONFIG`.

    ::

        import os
        os.environ["KCFG_KIVY_LOG_LEVEL"] = "warning"
        import kivy
        # during import it will map it to:
        # Config.set("kivy", "log_level", "warning")

    .. versionadded:: 1.11.0

KIVY_NO_ENV_CONFIG
    If set, no environment key will be mapped to configuration object.
    If unset, any `KCFG_section_key=value` will be mapped to Config.

    .. versionadded:: 1.11.0

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

    Values: gstplayer, ffpyplayer, ffmpeg, null

KIVY_AUDIO
    Implementation to use for playing audio

    Values: sdl2, gstplayer, ffpyplayer, pygame, avplayer

KIVY_IMAGE
    Implementation to use for reading image

    Values: sdl2, pil, pygame, imageio, tex, dds

    .. versionchanged:: 2.0.0
    Removed GPL `gif` implementation

KIVY_CAMERA
    Implementation to use for reading camera

    Values: avfoundation, android, opencv

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

KIVY_GL_BACKEND
    The OpenGL backend to use. See :mod:`~kivy.graphics.cgl`.

KIVY_GL_DEBUG
    Whether to log OpenGL calls. See :mod:`~kivy.graphics.cgl`.

KIVY_GRAPHICS
    Whether to use OpenGL ES2. See :mod:`~kivy.graphics.cgl`.

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
    Change the default Raspberry Pi display to use when using the egl_rpi
    window provider. The list of available value is accessible in 
    `vc_dispmanx_types.h`. Default value is 0:

    - 0: DISPMANX_ID_MAIN_LCD
    - 1: DISPMANX_ID_AUX_LCD
    - 2: DISPMANX_ID_HDMI
    - 3: DISPMANX_ID_SDTV
    - 4: DISPMANX_ID_FORCE_LCD
    - 5: DISPMANX_ID_FORCE_TV
    - 6: DISPMANX_ID_FORCE_OTHER

KIVY_BCM_DISPMANX_LAYER
    Change the default Raspberry Pi dispmanx layer when using the egl_rpi
    window provider. Default value is 0.

    .. versionadded:: 1.10.1

Event Loop
----------

KIVY_EVENTLOOP
    Which async library should be used when the app is run in an asynchronous
    manner. See :mod:`kivy.app` for example usage.

    ``'asyncio'``: When the app is run in an asynchronous manner and the standard
        library asyncio package should be used. The default if not set.
    ``'trio'``: When the app is run in an asynchronous manner and the `trio`
        package should be used.

    .. versionadded:: 2.0.0

Create a package for Windows
============================

Packaging your application for the Windows platform can only be done inside the
Windows OS. The following process has been tested on Windows 7 and the portable
package of Kivy.

The package will be either 32 or 64 bits depending on which version of Python
you ran it with.

+-----------------------------------------------------------------------------+
| NOTE: Currently, packages for Windows can be generated with Python 2.7 and  |
| Python 3.3+. However, Python 3.3+ support is still experimental             |
+-----------------------------------------------------------------------------+

.. _packaging-windows-requirements:

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * PyInstaller 2.1 (`pip install pyinstaller`) for Python 2.7, and experimental
      PyInstaller 3.0 (`pip install https://github.com/pyinstaller/pyinstaller/archive/python3.zip`)
      for Python 3.3+.

.. _Create-the-spec-file:

Create the spec file
--------------------

.. note::
    The following instructions is written for python 2.7, for other versions of
    python one should replace all instances of 2.7 or 27 with the appropriate
    version.

For this example, we'll package the touchtracer example and embed a custom icon.
The touchtracer example is the `kivy27\\examples\\demo\\touchtracer` directory and
the main file is named `main.py`.

#. Double click on the Kivy-2.7.bat and a console will open.
#. Create a folder into which the packaged app will be created and create the
   initial spec. For example create a TouchApp directory in the same directory
   as Kivy-2.7.bat and do::

    cd TouchApp
    pyinstaller --name touchtracer ..\kivy27\examples\demo\touchtracer\main.py

   You can also add an `icon.ico` file to the application folder in order to create an icon
   for the executable. If you don't have a .ico file available, you can convert your
   `icon.png` file to ico using the web app `ConvertICO <http://www.convertico.com>`_.
   Save the `icon.ico` in the touchtracer directory and type::

    pyinstaller --name touchtracer --icon ..\kivy27\examples\demo\touchtracer\icon.ico ..\kivy27\examples\demo\touchtracer\main.py

   For more options, please consult the
   `PyInstaller 2.1 Manual <http://pythonhosted.org/PyInstaller/>`_.

#. The spec file will be `touchtracer.spec` located in TouchApp. Now we need to
   edit the spec file to add kivy hooks to correctly build the exe.
   Open the spec file with your favorite editor and add theses lines at the
   beginning of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    import os
    install_hooks(globals())

   In the `Analysis()` function, remove the `hookspath=None` parameter.
   If you don't do this, the kivy package hook will not be used at all.

   Then you need to change the `COLLECT()` call to add the data for touchtracer
   (`touchtracer.kv`, `particle.png`, ...). Change the line to add a `Tree()`
   object. This Tree will search and add every file found in the touchtracer
   directory to your final package::

    coll = COLLECT( exe, Tree('../kivy27/examples/demo/touchtracer/'),
                   a.binaries,
                   #...
                   )

   If SDL2 is used the SDL2 dlls also needs to be included; so add the following
   Tree object to collect::

    Tree([f for f in os.environ.get('KIVY_SDL2_PATH', '').split(';') if 'bin' in f][0])

.. note::

    Until 1.9.0, the windows distribution used PyGame for the core providers.
    From 1.9.0 and on, the windows distribution uses SDL2 instead and does not
    come with a PyGame installation. If you're using the 1.8.0 package with 1.9.0
    or later code, or if you're using the 1.9.0 or later package, but downloaded
    and need PyGame in your packaging app, you'll have to add the following code
    to your spec file due to kivy issue #1638. After the imports add the following::

        def getResource(identifier, *args, **kwargs):
            if identifier == 'pygame_icon.tiff':
                raise IOError()
            return _original_getResource(identifier, *args, **kwargs)

        import pygame.pkgdata
        _original_getResource = pygame.pkgdata.getResource
        pygame.pkgdata.getResource = getResource

#. We are done. Your spec is ready to be executed!

.. _Build-the-spec:

Build the spec
--------------

#. Double click on `Kivy-2.7.bat`
#. Go to the TouchApp directory, and build the spec::

    cd TouchApp
    pyinstaller touchtracer.spec

#. The package will be in the `TouchApp\\dist\\touchtracer` directory.

Including Gstreamer
-------------------

If you wish to use Gstreamer, you'll need to further modify the spec file.

#. Kivy does some magic when trying to find which version of gstreamer
   and its bindings are available. In order for pyinstaller to find the
   correct gstreamer modules, you have to import core.video in the spec file
   before doing anything::

       from kivy.tools.packaging.pyinstaller_hooks import install_hooks
       import kivy.core.video

#. You'll need to include the gstreamer directory, found in the kivy distribution,
   in the COLLECT call. You can specify the direct path, or get it from the
   environment. In addition, the contents of the gstreamer/bin directory
   need to be included in the top level directory, otherwise the build process
   may have trouble finding dlls (this will create a second copy of the contents
   of bin)::

       import os
       gst_plugin_path = os.environ.get('GST_PLUGIN_PATH').split('lib')[0]
       COLLECT(exe, Tree(...),
               Tree(gst_plugin_path),
               Tree(os.path.join(gst_plugin_path, 'bin')),
               ...)

Following is an example of how to bundle the videoplayer at `kivy27/examples/widgets/videoplayer.py`.
From kivy-2.7.bat. Create the VideoPlayer directory alongside kivy-2.7.bat::

    cd VideoPlayer
    pyinstaller --name gstvideo ..\kivy27\examples\widgets\videoplayer.py

Now edit the spec file. At the top of the file add::

    import os
    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    import kivy.core.video

    install_hooks(globals())
    gst_plugin_path = os.environ.get('GST_PLUGIN_PATH').split('lib')[0]

Remove the `hookspath=None` parameter, and change::

    coll = COLLECT(exe,
                   a.binaries,
                   ...

to (remove the SDL2 part if SDL2 is not used)::

    coll = COLLECT(exe, Tree('../kivy27/examples/widgets'),
                   Tree([f for f in os.environ.get('KIVY_SDL2_PATH', '').split(';') if 'bin' in f][0]),
                   Tree(gst_plugin_path),
                   Tree(os.path.join(gst_plugin_path, 'bin')),
                   a.binaries,
                   ...

This will include gstreamer and the example video files in examples/widgets.
To build, run::

    pyinstaller gstvideo.spec

Then you should find gstvideo.exe in `VideoPlayer\\dist\\gstvideo`,
which when run will play a video.

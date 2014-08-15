Create a package for Windows
============================

Packaging your application for the Windows platform can only be done inside the
Windows OS. The following process has been tested on Windows 7 and the portable
package of Kivy.

The package will be either 32 or 64 bits depending on which version of Python
you ran it with.

+-------------------------------------------------------------------------------------------------------------------+
| NOTE: Currently, packages for Windows can only be generated with Python 2.7. Python 3.3+ support is on the way... |
+-------------------------------------------------------------------------------------------------------------------+

.. _packaging-windows-requirements:

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * `PyInstaller 2.1 <http://www.pyinstaller.org/#Downloads>`_

.. _Create-the-spec-file:

Create the spec file
--------------------

For this example, we'll package the touchtracer example and embed a custom icon.
The touchtracer example is the `kivy\\examples\\demo\\touchtracer` directory and
the main file is named `main.py`.

#. Double click on the Kivy.bat and a console will open.
#. Go to the pyinstaller 2.1 directory and create the initial spec::

    cd pyinstaller-2.1
    python pyinstaller.py --name touchtracer ..\kivy\examples\demo\touchtracer\main.py

   You can also add an `icon.ico` file to the application folder in order to create an icon
   for the executable. If you don't have a .ico file available, you can convert your
   `icon.png` file to ico using the web app `ConvertICO <http://www.convertico.com>`_.
   Save the `icon.ico` in the touchtracer directory and type::

    python pyinstaller.py --name touchtracer --icon ..\kivy\examples\demo\touchtracer\icon.ico ..\kivy\examples\demo\touchtracer\main.py

   For more options, please consult the
   `PyInstaller 2 Manual <http://www.pyinstaller.org/export/v2.1/project/doc/Manual.html?format=raw>`_.

#. The spec file will be `touchtracer.spec` located in inside the
   pyinstaller + `\touchtracer` directory. Now we need to edit the spec file to add
   kivy hooks to correctly build the exe.
   Open the spec file with your favorite editor and add theses lines at the
   beginning of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    install_hooks(globals())

   In the `Analysis()` function, remove the `hookspath=None` parameter.
   If you don't do this, the kivy package hook will not be used at all.

   Then you need to change the `COLLECT()` call to add the data for touchtracer
   (`touchtracer.kv`, `particle.png`, ...). Change the line to add a `Tree()`
   object. This Tree will search and add every file found in the touchtracer
   directory to your final package::

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   a.binaries,
                   #...
                   )

#. We are done. Your spec is ready to be executed!

.. _Build-the-spec:

Build the spec
--------------

#. Double click on `Kivy.bat`
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-2.1
    python pyinstaller.py touchtracer\touchtracer.spec

#. The package will be in the `touchtracer\\dist\\touchtracer` directory.

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

Following is an example of how to bundle the videoplayer at `kivy/examples/widgets/videoplayer.py`.
From kivy.bat::

    cd pyinstaller-2.1
    python pyinstaller.py --name gstvideo ..\kivy\examples\widgets\videoplayer.py

Now edit the spec file. At the top of the file add::

    import os
    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    import kivy.core.video

    install_hooks(globals())
    gst_plugin_path = os.environ.get('GST_PLUGIN_PATH').split('lib')[0]

Remove the hookspath parameter, and change::

    coll = COLLECT(exe,
                   a.binaries,
                   ...

to::

    coll = COLLECT(exe, Tree('../kivy/examples/widgets'),
                   Tree(gst_plugin_path),
                   Tree(os.path.join(gst_plugin_path, 'bin')),
                   a.binaries,
                   ...

This will include gstreamer and the example video files in examples/widgets.
To build, run::

    python pyinstaller.py gstvideo/gstvideo.spec

Then you should find gstvideo.exe in PyInstaller-2.1/gstvideo/dist/gstvideo,
which when run will play a video.

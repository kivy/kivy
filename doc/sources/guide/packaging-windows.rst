Create a package for Windows
============================

Packaging your application for the Windows platform can only be done inside the
Windows OS. The following process has only been tested inside VirtualBox using
Windows 7 and the portable package of Kivy.

The package will be 32 bits but can be run on both 32 and 64 bit Windows
platforms.

.. _packaging-windows-requirements:

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * `PyInstaller 2.0 <http://www.pyinstaller.org/#Downloads>`_

.. _Create-the-spec-file:

Create the spec file
--------------------

For this example, we'll package the touchtracer example and embed a custom icon.
The touchtracer example is the `kivy\examples\demo\touchtracer` directory, and
the main file is named `main.py`.

#. Double click on the Kivy.bat and a console will open.
#. Go to the pyinstaller 2.0 directory, and create the initial specs::

    cd pyinstaller-2.0
    python pyinstaller.py --name touchtracer ..\kivy\examples\demo\touchtracer\main.py

   You can also add an `icon.ico` file to the application folder in order to create an icon
   for the executable. If you don't have an .ico file available, you can convert your
   `icon.png` file to ico using the web app `ConvertICO <http://www.convertico.com>`_.
   Save the `icon.ico` in the touchtracer dxirectory and type::

    python pyinstaller.py --name touchtracer --icon ..\kivy\examples\demo\touchtracer\icon.ico ..\kivy\examples\demo\touchtracer\main.py

   For more options, please consult the
   `PyInstaller 2 Manual <http://www.pyinstaller.org/export/v2.0/project/doc/Manual.html?format=raw>`_.
    
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

    cd pyinstaller-2.0
    python pyinstaller.py touchtracer\touchtracer.spec

#. The package will be in the `touchtracer\dist\touchtracer` directory.


Including Gstreamer
-------------------

If you wish to use Gstreamer, please refer to the most up-to-date documentation
in :doc:`packaging-macosx`.

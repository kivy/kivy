Create package for Windows
==========================

Packaging your application for Windows platform can be done only inside the
Windows OS. The following method have been tested only inside VirtualBox and
Windows Seven, using the portable package of Kivy.

The package will be 32 bits, and can be run on both 32/64 bits windows
platform.

.. _packaging-windows-requirements:

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * PyInstaller 2.0: http://www.pyinstaller.org/#Downloads

.. _Create-the-spec-file:

Create the spec file
--------------------

For the example, we'll package touchtracer example, using a custom icon. The
touchtracer is the `kivy/examples/demo/touchtracer/` directory, and the main
file is named `main.py`

#. Double click on the Kivy.bat, a console will open
#. Go to the pyinstaller 2.0 directory, and create the initial specs::

    cd pyinstaller-2.0
    python pyinstaller.py --name touchtracer ..\kivy\examples\demo\touchtracer\main.py

   Alternatively, you can add an icon.ico to the main executable. If you don't have an .ico file available, you can convert your icon.png file to ico with the http://www.convertico.com/. Save the icon.ico in the touchtracer directory and do::

    python pyinstaller.py --name touchtracer --icon ..\kivy\examples\demo\touchtracer\icon.ico ..\kivy\examples\demo\touchtracer\main.py

#. The specs file is located on `touchtracer/touchtracer.spec` inside the
   pyinstaller directory. Now we need to edit the spec file to add kivy hooks
   to correctly build the exe.
   Open the spec file with your favorite editor and put theses lines at the
   start of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    install_hooks(globals())

   In the `Analysis()` command, remove the `hookspath=None` parameters.
   Otherwise, the kivy package hook will not be used at all.

   Then, you need to change the `COLLECT()` call to add the data of touchtracer
   (`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
   object. This Tree will search and add every file found in the touchtracer
   directory to your final package::

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   a.binaries,
                   #...
                   )

#. This is done, your spec is ready to be executed !

.. _Build-the-spec:

Build the spec
--------------

#. Double click on Kivy.bat
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-2.0
    python Build.py touchtracer\\touchtracer.spec

#. The package will be in the `touchtracer\\dist\\touchtracer` directory !


Including Gstreamer
-------------------

If you wish to use Gstreamer, refer to the most up-to-date documentation in the
:doc:`packaging-macosx`.

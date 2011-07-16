Create package for Windows
==========================

Packaging your application for Windows platform can be done only inside the
Windows OS. The following method have been tested only inside VirtualBox and
Windows Seven, using the portable package of Kivy.

The package will be 32 bits, and can be runned on both 32/64 bits windows
platform.

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * PyInstaller 1.5: http://www.pyinstaller.org/#Downloads

Install and configure PyInstaller
---------------------------------

#. Decompress the PyInstaller in the Kivy portable package
#. Double click on the Kivy.bat, a console will be open
#. Go to the pyinstaller directory, and run only once the Configure.py::

    cd pyinstaller-1.5
    python Configure.py

Create the spec file
--------------------

For the example, we'll package touchtracer example, using a custom icon. The
touchtracer is the `kivy/examples/demo/touchtracer/` directory, and the main
file is named `main.py`

#. Double click on the Kivy.bat, a console will be open
#. Go to the pyinstaller directory, and create the initial specs::

    cd pyinstaller-1.5
    python Makespec.py --name touchtracer ..\kivy\examples\demo\touchtracer\main.py

   Alternatively, you can add an icon.ico to the main executable. If you don't have any .ico file available, you can convert your icon.png file to ico with the http://www.convertico.com/. Save the icon.ico in the touchtracer directory and do::

    python Makespec.py --name touchtracer --icon ..\kivy\examples\demo\touchtracer\icon.ico ..\kivy\examples\demo\touchtracer\main.py

#. The specs file is located on `touchtracer/touchtracer.spec` inside the
   pyinstaller directory. Now we need to edit the spec file to add kivy hooks
   for correctly build the exe.
   Open the spec file with your favorite editor and put theses lines at the
   start of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    install_hooks(globals())

   Then, you need to change the `COLLECT()` call to add the data of touchtracer
   (`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
   object. This Tree will search and add every files found in the touchtracer
   directory to your final package::

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   a.binaries,
                   #...
                   )

#. This is done, your spec is ready to be executed !

Build the spec
--------------

#. Double click on Kivy.bat
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-1.5
    python Build.py touchtracer\\touchtracer.spec

#. The package will be the `touchtracer\\dist\\touchtracer` directory !


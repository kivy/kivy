Create package for MacOSX
=========================

Packaging your application for the MacOSX 10.6 platform can be done only inside
MacOSX. The following method has only been tested inside VirtualBox and
MacOSX 10.6, using the portable package of Kivy.

The package will be only for 64 bits MacOSX. We have no way to do 32 bits right
now, since we are not supporting 32 bits MacOSX platform.

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * PyInstaller 1.5: http://www.pyinstaller.org/#Downloads

Install and configure PyInstaller
---------------------------------

First, we need to correctly setup pyinstaller for 64 bits if you want to be
able to package your Kivy application.

#. Decompress the PyInstaller
#. Open a console, and go to the pyinstaller-1.5 directory
#. Execute the following::

    VERSIONER_PYTHON_PREFER_32_BIT=yes python Configure.py
    mkdir -p support/loader/Darwin-64bit
    pushd support/loader/Darwin-64bit
    wget http://www.pyinstaller.org/export/1488/trunk/support/loader/Darwin-64bit/run
    wget http://www.pyinstaller.org/export/1488/trunk/support/loader/Darwin-64bit/run_d
    wget http://www.pyinstaller.org/export/1488/trunk/support/loader/Darwin-64bit/runw
    wget http://www.pyinstaller.org/export/1488/trunk/support/loader/Darwin-64bit/runw_d
    chmod +x run*
    popd

Now, your pyinstaller installation is ready to be used !

Create the spec file
--------------------

For an example, we'll package the touchtracer example, using a custom icon. The
touchtracer is in the `../kivy/examples/demo/touchtracer/` directory, and the main
file is named `main.py`. Replace both path/filename according to your system.

#. Open a console
#. Go to the pyinstaller directory, and create the initial specs::

    cd pyinstaller-1.5
    python Makespec.py --name touchtracer ../kivy/examples/demo/touchtracer/main.py

#. The specs file is located on `touchtracer/touchtracer.spec` inside the
   pyinstaller directory. Now we need to edit the spec file to add kivy hooks
   to correctly build the exe.
   Open the spec file with your favorite editor and put theses lines at the
   start of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    install_hooks(globals())

   Then, you need to change the `COLLECT()` call to add the data of touchtracer
   (`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
   object. This Tree will search and add every file found in the touchtracer
   directory to your final package::

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   a.binaries,
                   #...
                   )

#. This is done, your spec is ready to be executed !

Build the spec and create DMG
-----------------------------

#. Open a console
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-1.5
    python Build.py touchtracer/touchtracer.spec

#. The package will be the `touchtracer/dist/touchtracer` directory. Rename it to .app::

    pushd touchtracer/dist
    mv touchtracer touchtracer.app
    hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    popd

#. You will have a Touchtracer.dmg available in the `touchtracer/dist` directory


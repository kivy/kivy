Create package for MacOSX
=========================

Packaging your application for the MacOSX 10.6 platform can be done only inside
MacOSX. The following method has only been tested inside VirtualBox and
MacOSX 10.6, using the portable package of Kivy.

The package will be only for 64 bits MacOSX. We have no way to do 32 bits right
now, since we are not supporting 32 bits MacOSX platform.

.. _mac_osx_requirements:

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * PyInstaller 2.0: http://www.pyinstaller.org/#Downloads

Ensure you've installed Kivy DMG and installed make-symlink script. `kivy`
command must be accessible from the command line.

Then, download and decompress the PyInstaller 2.0.

.. warning::

    It seem that latest PyInstaller has a bug when reading Mach-O binaries.
    (http://www.pyinstaller.org/ticket/614). To fix the issues, you can::

        cd pyinstaller-2.0/PyInstaller/lib/macholib
        curl -O https://bitbucket.org/ronaldoussoren/macholib/raw/e32d04b5361950a9343ca453d75602b65787f290/macholib/mach_o.py
        
    And then, the issue should be gone. It should be ok in the 2.1.


.. _mac_Create-the-spec-file:

Create the spec file
--------------------

For an example, we'll package the touchtracer example, using a custom icon. The
touchtracer is in the `../kivy/examples/demo/touchtracer/` directory, and the main
file is named `main.py`. Replace both path/filename according to your system.

#. Open a console
#. Go to the pyinstaller directory, and create the initial specs::

    cd pyinstaller-2.0
    kivy pyinstaller.py --name touchtracer ../kivy/examples/demo/touchtracer/main.py

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

.. _Build the spec and create DMG:

Build the spec and create DMG
-----------------------------

#. Open a console
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-2.0
    kivy pyinstaller.py touchtracer/touchtracer.spec

#. The package will be the `touchtracer/dist/touchtracer` directory. Rename it to .app::

    pushd touchtracer/dist
    mv touchtracer touchtracer.app
    hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    popd

#. You will have a Touchtracer.dmg available in the `touchtracer/dist` directory

Including Gstreamer
-------------------

If you wanted to read video files, audio, or camera, you would need to include
gstreamer. By default, only pygst/gst are discovered, but all the gst plugins
and libraries are missing. You need to include them in your .spec file too, by
adding one more argument to the `COLLECT()` method::

    import os
    gst_plugin_path = os.environ.get('GST_PLUGIN_PATH').split(':')[0]

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   Tree(os.path.join(gst_plugin_path, '..')),
                   a.binaries,
                   #...
                   )

For Kivy.app < 1.4.1, you also need to update one script included in our
Kivy.app. Go to
`/Applications/Kivy.app/Contents/Resources/kivy/kivy/tools/packaging/pyinstaller_hooks/`,
and edit the file named `rt-hook-kivy.py`, and add this line at the end::

    environ['GST_PLUGIN_PATH'] = join(root, '..', 'gst-plugins')


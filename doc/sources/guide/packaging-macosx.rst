Creating packages for MacOSX
============================

Packaging your application for the MacOSX 10.6 platform can only be done inside
MacOSX. The following method has only been tested inside VirtualBox and
MacOSX 10.6, using the portable package of Kivy.

The package will only work for the 64 bit MacOSX. We no longer support 32 bit
MacOSX platforms.

.. _mac_osx_requirements:

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * `PyInstaller 2.0 <http://www.pyinstaller.org/#Downloads>`_::
	
		pip install pyinstaller

Please ensure that you have installed the Kivy DMG and installed the `make-symlink` script.
The `kivy` command must be accessible from the command line.

Thereafter, download and decompress the PyInstaller 2.0 package.

.. warning::

    It seems that the latest PyInstaller has a bug affecting Mach-O binaries.
    (http://www.pyinstaller.org/ticket/614). To correct the issue, type::

        cd pyinstaller-2.0/PyInstaller/lib/macholib
        curl -O https://bitbucket.org/ronaldoussoren/macholib/raw/e32d04b5361950a9343ca453d75602b65787f290/macholib/mach_o.py
        
    In version 2.1, the issue has already been corrected.


.. _mac_Create-the-spec-file:

Create the spec file
--------------------

As an example, we'll package the touchtracer demo, using a custom icon. The
touchtracer code is in the `../kivy/examples/demo/touchtracer/` directory, and the main
file is named `main.py`. Replace both path/filename according to your system.

#. Open a console.
#. Go to the pyinstaller directory, and create the initial spec::

    cd pyinstaller-2.0
    kivy pyinstaller.py --windowed --name touchtracer ../kivy/examples/demo/touchtracer/main.py

#. The spec file is named `touchtracer.spec` and located inside the
   pyinstaller + `touchtracer` directory. Now we need to edit the spec file to add kivy hooks
   to correctly build the executable.
   Open the spec file with your favorite editor and put theses lines at the
   start of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    install_hooks(globals())

#. In the `Analysis()` method, remove the `hookspath=None` parameter.
   If you don't do this, the kivy package hook will not be used at all.

#. You now need to enable the data files to be packaged into the output. At the top of
   your spec file, add a function to collect the kv and png files::
   
	   def addDataFiles():
		allFiles = Tree('../kivy/examples/demo/touchtracer/')
		extraDatas = []
		for file in allFiles:
			if file[0].endswith('.kv') | file[0].endswith('.png'):
				print "Adding datafile: " + file[0]
				extraDatas.append(file)
		return extraDatas

   After the call to the Analysis function, append the data to it::
	
		a.datas += addDataFiles()

#. We are done. Your spec is ready to be executed!

.. _Build the spec and create DMG:

Build the spec and create a DMG
-------------------------------

#. Open a console.
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-2.0
    kivy pyinstaller.py touchtracer/touchtracer.spec

#. The package will be the `touchtracer/dist/touchtracer` directory. Rename it to .app::

    pushd touchtracer/dist
    mv touchtracer touchtracer.app
    hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    popd

#. You will now have a Touchtracer.dmg available in the `touchtracer/dist` directory.

Including Gstreamer
-------------------

If you want to read video files, audio, or camera, you will need to include
gstreamer. By default, only pygst/gst files are discovered, but all the gst plugins
and libraries are missing. You need to include them in your .spec file too, by
adding one more arguments to the `COLLECT()` method::

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


Create a package for Windows
============================

.. note::

    This document only applies for kivy ``1.9.1`` and greater.

Packaging your application for the Windows platform can only be done inside the
Windows OS. The following process has been tested on Windows with the Kivy
**wheels**.

The package will be either 32 or 64 bits depending on which version of Python
you ran it with.

.. _packaging-windows-requirements:

Requirements
------------

    * Latest Kivy (installed as described in :ref:`installation_windows`).
    * PyInstaller 3.1+ (``pip install --upgrade pyinstaller``).

.. _Create-the-spec-file:

Packaging a simple app
----------------------

For this example, we'll package the **touchtracer** example project and embed a custom icon.
The location of the kivy examples is, when using the wheels, installed to ``python\\share\\kivy-examples``
and when using the github source code installed as ``kivy\\examples``. We'll just refer to the full
path leading to the examples as ``examples-path``. The touchtracer example is in
``examples-path\\demo\\touchtracer`` and the main file is named ``main.py``.

#. Open your command line shell and ensure that python is on the path (i.e. ``python`` works).
#. Create a folder into which the packaged app will be created. For example create a ``TouchApp``
   folder and _`change to that directory <http://www.computerhope.com/cdhlp.htm>`_ with e.g.
   ``cd TouchApp``. Then type::

    python -m PyInstaller --name touchtracer examples-path\demo\touchtracer\main.py

   You can also add an `icon.ico` file to the application folder in order to create an icon
   for the executable. If you don't have a .ico file available, you can convert your
   `icon.png` file to ico using the web app `ConvertICO <http://www.convertico.com>`_.
   Save the `icon.ico` in the touchtracer directory and type::

    python -m PyInstaller --name touchtracer --icon examples-path\demo\touchtracer\icon.ico examples-path\demo\touchtracer\main.py

   For more options, please consult the
   `PyInstaller Manual <http://pythonhosted.org/PyInstaller/>`_.

#. The spec file will be ``touchtracer.spec`` located in ``TouchApp``. Now we need to
   edit the spec file to add the dependencies hooks to correctly build the exe.
   Open the spec file with your favorite editor and add these lines at the
   beginning of the spec (assuming sdl2 is used, the default now)::

    from kivy.deps import sdl2, glew

   Then, find ``COLLECT()`` and add the data for touchtracer
   (`touchtracer.kv`, `particle.png`, ...): Change the line to add a ``Tree()``
   object, e.g. ``Tree('examples-path\\demo\\touchtracer\\')``. This Tree will
   search and add every file found in the touchtracer directory to your final package.

   To add the dependencies, before the first keyword argument in COLLECT add a
   Tree object for every path of the dependecies. E.g.
   ``*[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)]`` so it'll look something like::

    coll = COLLECT(exe, Tree('examples-path\\demo\\touchtracer\\'),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
                   strip=False,
                   upx=True,
                   name='touchtracer')

#. Now we build the spec file in ``TouchApp`` with::

    python -m PyInstaller touchtracer.spec

#. The compiled package will be in the `TouchApp\\dist\\touchtracer` directory.

Packaging a video app
---------------------

Following we'll slightly modify the example above to package a app that uses gstreamer
for video. We'll use the ``videoplayer`` example found at ``examples-path\widgets\videoplayer.py``.
Create a folder somewhere called ``VideoPlayer`` and on the command line change your current
directory to that folder and do::

    python -m PyInstaller --name gstvideo examples-path\widgets\videoplayer.py

to create the ``gstvideo.spec`` file. Edit as above and this time include the
gstreamer dependency as well::

    from kivy.deps import sdl2, glew, gstreamer

and add the ``Tree()`` to include the video files, e.g. ``Tree('examples-path\\widgets')``
as well as the gstreamer dependencies so it should look something like::

    coll = COLLECT(exe, Tree('examples-path\\widgets'),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + gstreamer.dep_bins)],
                   strip=False,
                   upx=True,
                   name='gstvideo')

Then build the spec file in ``VideoPlayer`` with::

    python -m PyInstaller gstvideo.spec

and you should find gstvideo.exe in ``VideoPlayer\dist\gstvideo``,
which when run will play a video.

.. note::

    If you're using Pygame and need PyGame in your packaging app, you'll have to add the
    following code to your spec file due to kivy issue #1638. After the imports add the
    following::

        def getResource(identifier, *args, **kwargs):
            if identifier == 'pygame_icon.tiff':
                raise IOError()
            return _original_getResource(identifier, *args, **kwargs)

        import pygame.pkgdata
        _original_getResource = pygame.pkgdata.getResource
        pygame.pkgdata.getResource = getResource

Including/excluding video and audio and reducing app size
-------------------------------------------------------

PyInstaller includes a hook for kivy that by default adds the core modules
used by kivy, e.g. audio, video, spelling etc (you still need to package
the gstreamer dlls manually with ``Tree()`` - see the example above). To reduce
app size, some of these modules may be excluded, e.g. if no audio/video is used.

To manually exclude some core providers, one can use
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_kivy_providers` or
:func:`~kivy.tools.packaging.pyinstaller_hooks.list_hiddenimports`. See
:mod:`~kivy.tools.packaging.pyinstaller_hooks` for details. Following is
the touchtracer example modified to exclude all video and audio making
a much smaller app.

Add the import statement
``from kivy.tools.packaging.pyinstaller_hooks import  get_kivy_providers, hookspath``
and modify ``Analysis`` as follows::

    a = Analysis(['examples-path\\demo\\touchtracer\\main.py'],
                 ...
                 hookspath=hookspath(),
                 runtime_hooks=[],
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=block_cipher,
                 **get_kivy_providers(video=None, audio=None))

The key points is to provide the alternate
:func:`~kivy.tools.packaging.pyinstaller_hooks.hookspath` which does not list
by default all the kivy providers and instead manually to hiddenimports
add the required providers while removing the undesired ones (audio and
video in this example) with
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_kivy_providers`.

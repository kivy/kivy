.. _packaging-win:

Create a package for Windows
============================

.. note::

    This document only applies for kivy ``1.9.1`` and greater.

Packaging your application for the Windows platform can only be done inside the
Windows OS. The following process has been tested on Windows with the Kivy
**wheels** installation, see at the end for alternate installations.

The package will be either 32 or 64 bits depending on which version of Python
you ran it with.

.. _packaging-windows-requirements:

Requirements
------------

    * Latest Kivy (installed as described in :ref:`installation_windows`).
    * PyInstaller 3.1+ (``pip install --upgrade pyinstaller``).

.. _Create-the-spec-file:

PyInstaller default hook
------------------------

This section applies to PyInstaller (>= 3.1) that includes the kivy hooks.
To overwrite the default hook the
following examples need to be slightly modified. See :ref:`overwrite-win-hook`.

Packaging a simple app
----------------------

For this example, we'll package the **touchtracer** example project and embed
a custom icon. The location of the kivy examples is, when using the wheels,
installed to ``python\\share\\kivy-examples`` and when using the github source
code installed as ``kivy\\examples``. We'll just refer to the full path leading
to the examples as ``examples-path``. The touchtracer example is in
``examples-path\\demo\\touchtracer`` and the main file is named ``main.py``.

#. Open your command line shell and ensure that python is on the path (i.e.
   ``python`` works).
#. Create a folder into which the packaged app will be created. For example
   create a ``TouchApp`` folder and `change to that directory
   <https://www.computerhope.com/cdhlp.htm>`_ with e.g. ``cd TouchApp``.
   Then type::

    python -m PyInstaller --name touchtracer examples-path\demo\touchtracer\main.py

   You can also add an `icon.ico` file to the application folder in order to
   create an icon for the executable. If you don't have a .ico file available,
   you can convert your `icon.png` file to ico using the web app
   `ConvertICO <https://www.convertico.com>`_. Save the `icon.ico` in the
   touchtracer directory and type::

    python -m PyInstaller --name touchtracer --icon examples-path\demo\touchtracer\icon.ico examples-path\demo\touchtracer\main.py

   For more options, please consult the
   `PyInstaller Manual <https://pyinstaller.readthedocs.io/en/stable/>`_.

#. The spec file will be ``touchtracer.spec`` located in ``TouchApp``. Now we
   need to edit the spec file to add the dependencies hooks to correctly build
   the exe. Open the spec file with your favorite editor and add these lines
   at the beginning of the spec (assuming sdl2 is used, the default now)::

    from kivy_deps import sdl2, glew

   Then, find ``COLLECT()`` and add the data for touchtracer
   (`touchtracer.kv`, `particle.png`, ...): Change the line to add a ``Tree()``
   object, e.g. ``Tree('examples-path\\demo\\touchtracer\\')``. This Tree will
   search and add every file found in the touchtracer directory to your final
   package.

   To add the dependencies, before the first keyword argument in COLLECT add a
   Tree object for every path of the dependencies. E.g.
   ``*[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)]`` so it'll look
   something like::

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

Single File Application
-----------------------

Next, we will modify the example above to package the **touchtracer** example project as a single file application. Following the same steps as above, instead issue the following command::

     python -m PyInstaller --onefile --name touchtracer examples-path\demo\touchtracer\main.py

#. As before, this will generate touchtracer.spec, which we will edit to add the dependencies. In this instance, edit the arguments to the EXE command so that it will look something like this::

     exe = EXE(pyz, Tree('examples-path\\demo\\touchtracer\\'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          upx=True,
          name='touchtracer')

#. Now you can build the spec file as before with::

     python -m PyInstaller touchtracer.spec

#. The compiled package will be in the `TouchApp\\dist` directory and will consist of a single executable file.

Bundling Data Files
-------------------

We will again modify the previous example to include bundled data files. PyInstaller allows inclusion of outside data files (such as images, databases, etc) that the project needs to run. When running an app on Windows, the executable extracts to a temporary folder which the Kivy project doesn't know about, so it can't locate these data files. We can fix that with a few lines.

#. First, follow PyInstaller documentation on how to include data files in your application.

#. Modify your main python code to include the following imports (if it doesn't have them already)::

     import os, sys
     from kivy.resources import resource_add_path, resource_find

#. Modify your main python code to include the following (using the **touchtracer** app as an example)::

     if __name__ == '__main__':
         if hasattr(sys, '_MEIPASS'):
             resource_add_path(os.path.join(sys._MEIPASS))
         TouchtracerApp().run()

#. Finally, follow the steps for bundling your application above.

Packaging a video app with gstreamer
------------------------------------

Following we'll slightly modify the example above to package a app that uses
gstreamer for video. We'll use the ``videoplayer`` example found at
``examples-path\widgets\videoplayer.py``. Create a folder somewhere called
``VideoPlayer`` and on the command line change your current directory to that
folder and do::

    python -m PyInstaller --name gstvideo examples-path\widgets\videoplayer.py

to create the ``gstvideo.spec`` file. Edit as above and this time include the
gstreamer dependency as well::

    from kivy_deps import sdl2, glew, gstreamer

and add the ``Tree()`` to include the video files, e.g.
``Tree('examples-path\\widgets')`` as well as the gstreamer dependencies so it
should look something like::

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

    If you're using Pygame and need PyGame in your packaging app, you'll have
    to add the following code to your spec file due to kivy issue #1638. After
    the imports add the following::

        def getResource(identifier, *args, **kwargs):
            if identifier == 'pygame_icon.tiff':
                raise IOError()
            return _original_getResource(identifier, *args, **kwargs)

        import pygame.pkgdata
        _original_getResource = pygame.pkgdata.getResource
        pygame.pkgdata.getResource = getResource

.. _overwrite-win-hook:

Overwriting the default hook
----------------------------

Including/excluding video and audio and reducing app size
---------------------------------------------------------

PyInstaller includes a hook for kivy that by default adds **all** the core
modules used by kivy, e.g. audio, video, spelling etc (you still need to
package the gstreamer dlls manually with ``Tree()`` - see the example above)
and their dependencies. If the hook is not installed or to reduce app size some
of these modules may be excluded, e.g. if no audio/video is used, with
an alternative hook.

Kivy provides the alternate hook at
:func:`~kivy.tools.packaging.pyinstaller_hooks.hookspath`. In addition, if and
only if PyInstaller doesn't have the default hooks
:func:`~kivy.tools.packaging.pyinstaller_hooks.runtime_hooks` must also be
provided. When overwriting the hook, the latter one typically is not required
to be overwritten.

The alternate :func:`~kivy.tools.packaging.pyinstaller_hooks.hookspath` hook
does not include any of the kivy providers. To add them, they have to be added
with
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_deps_minimal` or
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_deps_all`. See
their documentation and :mod:`~kivy.tools.packaging.pyinstaller_hooks` for more
details. But essentially,
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_deps_all` add all the
providers like in the default hook while
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_deps_minimal` only adds
those that are loaded when the app is run. Each method provides a list of
hidden kivy imports and excluded imports that can be passed on to ``Analysis``.

One can also generate a alternate hook which literally lists every kivy
provider module and those not required can be commented out. See
:mod:`~kivy.tools.packaging.pyinstaller_hooks`.

To use the the alternate hooks with the examples above modify as following to
add the hooks with ``hookspath()`` and ``runtime_hooks`` (if required)
and ``**get_deps_minimal()`` or ``**get_deps_all()`` to specify the providers.

For example, add the import statement::

 from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, get_deps_all, hookspath, runtime_hooks

and then modify ``Analysis`` as follows::

    a = Analysis(['examples-path\\demo\\touchtracer\\main.py'],
                 ...
                 hookspath=hookspath(),
                 runtime_hooks=runtime_hooks(),
                 ...
                 **get_deps_all())

to include everything like the default hook. Or::

    a = Analysis(['examples-path\\demo\\touchtracer\\main.py'],
                 ...
                 hookspath=hookspath(),
                 runtime_hooks=runtime_hooks(),
                 ...
                 **get_deps_minimal(video=None, audio=None))

e.g. to exclude the audio and video providers and for the other core modules
only use those loaded.

The key points is to provide the alternate
:func:`~kivy.tools.packaging.pyinstaller_hooks.hookspath` which does not list
by default all the kivy providers and instead manually to hiddenimports
add the required providers while removing the undesired ones (audio and
video in this example) with
:func:`~kivy.tools.packaging.pyinstaller_hooks.get_deps_minimal`.

Alternate installations
-----------------------

The previous examples used e.g.
``*[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + gstreamer.dep_bins)],``
to make PyInstaller add all the dlls used by these dependencies. If kivy
was not installed using the wheels method these commands will not work and e.g.
``kivy_deps.sdl2`` will fail to import. Instead, one must find the location
of these dlls and manually pass them to the ``Tree`` class in a similar fashion
as the example.

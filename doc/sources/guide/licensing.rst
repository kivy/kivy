Package licensing
=================

.. warning:: This is not a lawyer consulted guide! Kivy organisation, authors
   or contributors to this guide take no responsibility for any lack of
   information, misleading information presented here or any actions based on
   this guide. The guide is merely informative and is meant to protect
   inexperienced users.

Your code alone may not require including licensing info and copyright notices
of other used software, but binaries are something else. When a binary (.exe,
.app, .apk, ...) is created it includes Kivy, its dependencies and other
packages that your application uses. Some of them are licensed in a way they
require including a copyright notice somewhere in your app (or more). Before
distributing any of the binaries, please **check all the created files** that
don't belong to your source (.dll, .pyd, .so, ...) and include approperiate
copyright notices if required by the license the files belong to. This way you
should satisfy licensing requirements of the Kivy deps.

Dependencies
------------

All of the dependencies will jump out at least partially on each platform Kivy
supports, therefore you need to comply to their licenses, which mostly requires
only pasting a copyright notice to your app and not pretending you wrote the
code.

.. |mixer| replace:: SDL_mixer has them
.. _mixer: http://hg.libsdl.org/SDL_mixer/file/efa81a285f22/VisualC/external/lib/x86

* `docutils <https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/COPYING.txt>`_
* `pygments <https://bitbucket.org/birkenfeld/pygments-main/src/a042025b350cd9c9461f7385d9ba0f13cdb01bb9/LICENSE>`_
* `sdl2 <https://www.libsdl.org/license.php>`_
* `glew <http://glew.sourceforge.net/glew.txt>`_
* `gstreamer <https://github.com/GStreamer/gstreamer/blob/master/COPYING>`_
  (if used)
* image & audio libraries(e.g. |mixer|_)

You'll probably need to check image and audio libraries manually (mostly
begin with ``lib``). The ``LICENSE*`` files that belong to them should be
included by PyInstaller.

Windows (PyInstaller)
---------------------

.. |win32| replace:: pypiwin32
.. _win32: https://pypi.python.org/pypi/pypiwin32

To access Windows API, Kivy uses |win32|_ package. This package is released
under [PSF license](https://opensource.org/licenses/Python-2.0).

VS redistributables
~~~~~~~~~~~~~~~~~~~

.. |py2crt| replace:: Py2 CRT license
.. _py2crt: https://hg.python.org/sandbox/2.7/file/tip/Tools/msi/crtlicense.txt
.. |py3crt| replace:: Py3 CRT license
.. _py3crt: https://hg.python.org/cpython/file/tip/Tools/msi/exe/crtlicense.txt
.. |redist| replace:: List of redistributables
.. _redist: https://msdn.microsoft.com/en-us/library/8kche8ah(v=vs.90).aspx

Python compiled with Visual Studio (official) has some files from Microsoft
and you are required to protect them if you distribute them. You can do that
by including names of the files and a reworded version of |py2crt|_ or
|py3crt|_ depending which interpreter you use, so that it targets the end-user
of your application.

* |redist|_

Other libraries
~~~~~~~~~~~~~~~

* `zlib <https://github.com/madler/zlib/blob/master/README>`_

.. note:: Please add other libs that you *don't use directly* and are present
   after packaging with e.g. PyInstaller on Windows.

Linux
-----

Missing.

Mac
---

Missing.

iOS
---

Missing.

Android
-------

Missing.

(pygame license, etc)

RPi
---

Missing.

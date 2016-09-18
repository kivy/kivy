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
may satisfy licensing requirements of the Kivy deps.

Dependencies
------------

All of the dependencies will jump out at least partially on each platform Kivy
supports, therefore you need to comply to their licenses, which mostly requires
only pasting a copyright notice to your app and not pretending you wrote the
code.

.. |mixer| replace:: SDL_mixer has them
.. _mixer: http://hg.libsdl.org/SDL_mixer/file/default/VisualC/external/lib/x86
.. |dcutil| replace:: docutils
.. _dcutil: https://sf.net/p/docutils/code/HEAD/tree/trunk/docutils/COPYING.txt

* |dcutil|_
* `pygments <https://bitbucket.org/birkenfeld/pygments-main/src/tip/LICENSE>`_
* `sdl2 <https://www.libsdl.org/license.php>`_
* `glew <http://glew.sourceforge.net/glew.txt>`_
* `gstreamer <https://github.com/GStreamer/gstreamer/blob/master/COPYING>`_
  (if used)
* image & audio libraries(e.g. |mixer|_)

You'll probably need to check image and audio libraries manually (mostly begin
with ``lib``). The ``LICENSE*`` files that belong to them should be included by
PyInstaller, but are not by python-for-android and you need to find them.

Windows (PyInstaller)
---------------------

.. |win32| replace:: pypiwin32
.. _win32: https://pypi.python.org/pypi/pypiwin32

To access some Windows API features, Kivy uses |win32|_ package. This package
is released under `PSF license <https://opensource.org/licenses/Python-2.0>`_.

VS redistributables
~~~~~~~~~~~~~~~~~~~

.. |py2crt| replace:: Py2 CRT license
.. _py2crt: https://hg.python.org/sandbox/2.7/file/tip/Tools/msi/crtlicense.txt
.. |py3crt| replace:: Py3 CRT license
.. _py3crt: https://hg.python.org/cpython/file/tip/Tools/msi/exe/crtlicense.txt
.. |redist| replace:: List of redistributables
.. _redist: https://msdn.microsoft.com/en-us/library/8kche8ah(v=vs.90).aspx

Python compiled with Visual Studio (official) has some files from Microsoft and
you are allowed to redistribute them under specific conditions listed in the
CRTlicense. Including the names of the files and a reworded version of
|py2crt|_ or |py3crt|_ depending which interpreter you use, so that it targets
the end-user of your application may satisfy such requirements.

* |redist|_

Other libraries
~~~~~~~~~~~~~~~

* `zlib <https://github.com/madler/zlib/blob/master/README>`_

.. note:: Please add other libs that you *don't use directly* and are present
   after packaging with e.g. PyInstaller on Windows.

Linux
-----

.. |badsit| replace:: situation bad for your user
.. _badsit: avoid_

Linux has many distributions which means there's no correct guide for all of
the distributions. Under this part belongs RPi too. However, it can be
simplified into two ways of how to create a package (also with PyInstaller):
with or without including binaries.

If the binaries are included, you should check every file (e.g. `.so`) that's
not your source and find a license it belongs to. According to that license
you'll probably need to put an attribution into your application or even more.

If the binaries are excluded (which allows packaging your app as e.g. `.deb`
package), there's a |badsit|_. It's up to you to decide whether you satisfy
conditions of other licenses and for example including copyright attribution
into your app or not.

Android
-------

As APK is just an archive of files, you can extract files from it and (as in
Windows part) check all the files.

``APK/assets/private.mp3/private.mp3/`` contains all the included files. Most
of them are related to Kivy, Python or your source, but those that aren't need
checking.

Known packages:

* `pygame <https://bitbucket.org/pygame/pygame/src/tip/LGPL>`_
  (if old_toolchain is used)
* `sqlite3 <https://github.com/ghaering/pysqlite/blob/master/LICENSE>`_
* `six <https://bitbucket.org/gutworth/six/src/tip/LICENSE>`_

There are included libraries either Kivy directly or through Pygame/SDL2 uses,
those are located in ``APK/lib/armeabi/``. Most of them are related to
dependencies or are produced from python-for-android and are part of its source
(and licensing).

* libapplication.so

Mac
---

Missing.

iOS
---

Missing.

.. _avoid:

Avoiding binaries
-----------------

.. |cons| replace:: consequences
.. _cons: http://programmers.stackexchange.com/a/234295

There might be a way how to avoid this licensing process with avoiding creating
a distribution with third-party stuff completely. With Python you can create
a module, which is only your code with ``__main__.py`` + ``setup.py`` that only
lists required deps.

This way you can still distribute your app - your *code* - and you might not
need to care about other licenses. The combination of your code and the
dependencies could be specified as a "usage" rather than a "distribution". The
responsibility of satisfying licenses, however, most likely transfers to your
user, who needs to assemble the environment to even run the module. If you care
about your users, you might want to slow down a little and read more about
|cons|_.

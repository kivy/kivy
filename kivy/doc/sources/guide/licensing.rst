Package licensing
=================

.. warning:: This is not a legally authoritative guide! The Kivy organisation,
   authors and contributors take no responsibility for any lack of knowledge,
   information or advice presented here. The guide is merely informative and is
   meant to protect inexperienced users.

Your code alone may not require including licensing information or copyright
notices of other included software, but binaries are something else. When a
binary (.exe, .app, .apk, ...) is created, it includes Kivy, its dependencies
and other packages that your application uses.

Some of them are licensed in a way that requires including a copyright notice
somewhere in your app (or more). Before
distributing any of the binaries, please **check all the created files** that
don't belong to your source (.dll, .pyd, .so, ...) and include the appropriate
copyright notices if required by the license the files belong to. This way you
may satisfy licensing requirements of the Kivy deps.

Dependencies
------------

All of the dependencies will be used at least partially on each platform Kivy
supports. You therefore need to comply to their licenses, which mostly requires
only pasting a copyright notice in your app and not pretending you wrote the
code.

.. |mixer| replace:: SDL_mixer has them
.. _mixer: https://github.com/libsdl-org/SDL_mixer/tree/master/external
.. |dcutil| replace:: docutils
.. _dcutil: https://docutils.sourceforge.io/COPYING.html

* |dcutil|_
* `pygments https://github.com/pygments/pygments/blob/master/LICENSE`_
* `sdl2 <https://www.libsdl.org/license.php>`_
* `glew <http://glew.sourceforge.net/glew.txt>`_
* `gstreamer <https://github.com/GStreamer/gstreamer/blob/master/COPYING>`_
  (if used)
* image & audio libraries(e.g. |mixer|_)

You'll probably need to check image and audio libraries manually (most begin
with ``lib``). The ``LICENSE*`` files that belong to them should be included by
PyInstaller, but are not included by python-for-android and you need to find
them.

Windows (PyInstaller)
---------------------

.. |win32| replace:: pypiwin32
.. _win32: https://pypi.python.org/pypi/pypiwin32

To access some Windows API features, Kivy uses the |win32|_ package. This
package is released under the
`PSF license <https://opensource.org/licenses/Python-2.0>`_.

Visual Studio Redistributables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. |py2crt| replace:: Py2 CRT license
.. _py2crt: https://hg.python.org/sandbox/2.7/file/tip/Tools/msi/crtlicense.txt
.. |py3crt| replace:: Py3 CRT license
.. _py3crt: https://hg.python.org/cpython/file/tip/Tools/msi/exe/crtlicense.txt
.. |redist| replace:: List of redistributables
.. _redist: https://msdn.microsoft.com/en-us/library/8kche8ah(v=vs.90).aspx

Python compiled with Visual Studio (official) includes files from Microsoft and
you are only allowed to redistribute them under specific conditions listed in
the CRTlicense. You need to include the names of the files and a reworded
version of |py2crt|_ or |py3crt|_ (depending which interpreter you use) and
present these to the end-user of your application in order to satisfy their
requirements.

* |redist|_

Other libraries
~~~~~~~~~~~~~~~

* `zlib <https://github.com/madler/zlib/blob/master/README>`_

.. note:: Please add the attributions for other libraries that you
   *don't use directly* but are present after packaging with e.g. PyInstaller
   on Windows.

Linux
-----

.. |badsit| replace:: situation bad for your user
.. _badsit: avoid_

Linux has many distributions which means there's no correct guide for all of
the distributions. This applies to the RPi too. However, it can be
simplified in two ways depending on how you create a package (also with
PyInstaller): with or without including binaries.

If the binaries are included, you should check every file (e.g. `.so`) that's
not your source and find the license it belongs to. According to that license,
you'll probably need to put an attribution into your application or possibly
more, depending on the requirements of that license.

If the binaries are not included (which allows packaging your app as e.g. a
`.deb` package), there's a |badsit|_. It's up to you to decide whether you
satisfy the conditions of other licenses and, for example, include copyright
attributions into your app or not.

Android
-------

As APK or AAB are just an archive of files: you can extract files from them and (as in
Windows redistributables) check all the files.

``private.tar`` contains all the included files. Most
of them are related to Kivy, Python or your source, but those that aren't need
checking.

**apk:** ``APK/assets/private.tar``

**aab:** ``AAB/base/assets/private.tar``

There are other included libraries, included either by Kivy directly or through
SDL2, that are located in ``APK/lib/*`` or ``AAB/base/lib/*``. Most of them are related
to dependencies or are produced by python-for-android and are part of its source
(and licensing).

.. warning::
    ``libpybundle.so`` is actually a ``tarball`` that contains python ``modules`` and ``site-packages``.
    You'll probably want to inspect it for licensing purposes via ``tar -xvf libpybundle.so``.

macOS
-----

Missing.

iOS
---

Missing.

.. _avoid:

Avoiding binaries
-----------------

.. |cons| replace:: consequences
.. _cons: http://programmers.stackexchange.com/a/234295

There might be a way how to avoid this licensing process by avoiding creating
a distribution with third-party stuff completely. With Python you can create
a module, which is only your code with ``__main__.py`` + ``setup.py`` that only
lists required dependencies.

This way, you can still distribute your app - your *code* - and you might not
need to care about other licenses. The combination of your code and the
dependencies could be specified as a "usage" rather than a "distribution". The
responsibility of satisfying licenses, however, most likely transfers to your
user, who needs to assemble the environment to even run the module. If you care
about your users, you might want to slow down a little and read more about the
|cons|_.

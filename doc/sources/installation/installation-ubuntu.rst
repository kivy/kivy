Installation on Ubuntu
======================

The following instructions are for Ubuntu, but they should work in a
similar fashion for other Linux distributions (e.g. Debian, opensuse,
fedora, etc.). Obviously you will need to adjust the commands.

Ubuntu 10.10 (Maverick)
-----------------------

Unfortunately there is no kivy package in the Ubuntu repositories yet.
We're working on it. Until then, do the following instead:

::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good cython python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev
    $ easy_install kivy

If you already installed kivy before, you can upgrade it with::

    $ easy_install -U kivy


.. _linux-run-app:

Start from Command Line
-----------------------

You can know run any example from the examples directory of kivy::

    $ cd <path to kivy directory>/examples/demo
    $ python touchtracer.py


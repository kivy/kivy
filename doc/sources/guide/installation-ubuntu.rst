Installation on Ubuntu
======================

Ubuntu 10.10 (Maverick)
-----------------------

::
    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good cython python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev
    $ easy_install kivy

If you already installed kivy before, you can upgrade it with::

    $ easy_install -U kivy

You can know run any example from the examples directory of kivy.

    $ cd <path to kivy directory>/examples/demo
    $ python touchtracer.py


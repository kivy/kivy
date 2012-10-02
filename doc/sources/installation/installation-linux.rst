.. _installation_linux:

Installation on Linux
=====================

Prerequisites
-------------

Ubuntu (11.10 or newer)
~~~~~~~~~~~~~~~~~~~~~~~

::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev python-pip
    $ sudo pip install --upgrade cython

Fedora (16)
~~~~~~~~~~~

::

    $ sudo yum install python-distutils-extra python-enchant freeglut PyOpenGL \
    SDL_ttf-devel SDL_mixer-devel pygame pygame-devel khrplatform-devel \
    mesa-libGLES mesa-libGLES-devel gstreamer-plugins-good gstreamer \
    gstreamer-python mtdev-devel python-pip
    $ sudo pip install --upgrade cython

OpenSuse (12.1)
~~~~~~~~~~~~~~~

::

    $ sudo zypper install python-distutils-extra python-pygame python-opengl \
    python-gstreamer-0_10 python-enchant gstreamer-0_10-plugins-good \
    python-devel Mesa-devel python-pip
    $ zypper install -t pattern devel_C_C++
    $ sudo pip install --upgrade cython


Mageia (1 and 2(cauldron))
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ su
    $ urpmi python-setuptools python-pygame python-opengl \
    gstreamer0.10-python python-enchant gstreamer0.10-plugins-good \
    python-cython lib64python-devel lib64mesagl1-devel lib64mesaegl1-devel \
    lib64mesaglesv2_2-devel make gcc
    $ sudo easy_install pip
    $ sudo pip install --upgrade cython


Installation
------------

If you're installing Kivy for the first time, do::

    $ sudo easy_install kivy

If you already installed kivy before, you can upgrade it with::

    $ sudo easy_install --upgrade kivy


.. _linux-run-app:

Start from Command Line
-----------------------

We are shipping some examples ready-to-run. However, theses examples are packaged inside the package. That's mean, you must known first where easy_install have installed your current kivy package, and go to the example directory::

    $ python -c "import pkg_resources; print pkg_resources.resource_filename('kivy', '../share/kivy-examples')"

And you should have a path similar to::

    /usr/local/lib/python2.6/dist-packages/Kivy-1.0.4_beta-py2.6-linux-x86_64.egg/share/kivy-examples/

Then you can go to the example directory, and run it::

    # launch touchtracer
    $ cd <path to kivy-examples>
    $ cd demo/touchtracer
    $ python main.py

    # launch pictures
    $ cd <path to kivy-examples>
    $ cd demo/pictures
    $ python main.py

If you don't know about Unix and symbolic link, you can create a link directly in your home directory, for an easier access. For example:

#. Get the example path from the command line above
#. Paste in your console::

    $ ln -s <path to kivy-examples> ~/

#. Then, you can access to kivy-examples directly in your Home directory::

    $ cd ~/kivy-examples

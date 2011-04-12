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

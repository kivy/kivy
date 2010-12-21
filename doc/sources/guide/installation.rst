.. _installation:

Installation
============

Kivy can use several libraries, but depend only of 1 dependencies : `Cython
<http://cython.org>`_ and `Numpy <http://numpy.scipy.org/>`_. If you want
support features like Window, Video or Spelling, you must install other
libraries. We are recommanding `Pygame <http://pygame.org>`_, `Gst-Python
<http://www.gstreamer.net/modules/gst-python.html>`_ and `Enchant
<http://www.rfk.id.au/software/pyenchant/>`_.

Optional libraries :

    * `OpenCV 2.0 <http://sourceforge.net/projects/opencvlibrary/>`_: camera
    * `PIL <http://www.pythonware.com/products/pil/index.htm>`_: image and text
    * `PyCairo <http://www.cairographics.org/pycairo/>`_: text
    * `PyEnchant <http://www.rfk.id.au/software/pyenchant/>`_: spelling
    * `Pygame <http://www.pygame.org>`_ : window, image, text and audio
    * `PyGST <http://gstreamer.freedesktop.org/ + http://pygstdocs.berlios.de/>`_: audio, video and camera


Stable version
--------------

No stable version yet.

Development version
-------------------

If you want to work with the latest version of Kivy, you must clone and use our source code from `Github <http://github.com/>`_.

Ubuntu
~~~~~~

::

    $ sudo apt-get install sudo apt-get install python-setuptools python-pygame python-opengl \
      python-numpy python-gst0.10 python-enchant gstreamer0.10-plugins-good cython python-dev \
      build-essential libgl1-mesa-dev libglu1-mesa-dev
    $ git checkout git://github.com/tito/kivy.git
    $ cd kivy
    $ python setup.py build
    $ sudo python setup.py install



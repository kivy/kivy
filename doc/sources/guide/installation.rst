.. _installation:

Installation
============

We try not to reinvent the wheel but bring something innovative to the
market. As a consequence, we're focused on our own code and use already
existing, high-qualitative third-party libraries where possible.
For the rich set of features that Kivy offers, several other libraries are
required. If you do not use a specific feature (e.g. video playback) you
don't need the corresponding dependency, however.
That said, there are two dependencies that Kivy **does** require:
`Cython <http://cython.org>`_ and `Numpy <http://numpy.scipy.org/>`_.
In addition, you need a `Python <http://python.org/>`_ 2.x (**not**  3.x)
interpreter. If you want to enable features like windowing (i.e., open a Window),
audio/video playback or spelling correction, you must install other
dependencies. For these, we recommend `Pygame <http://pygame.org>`_, `Gst-Python
<http://www.gstreamer.net/modules/gst-python.html>`_ and `Enchant
<http://www.rfk.id.au/software/pyenchant/>`_, respectively.

Other optional libraries (mutually interchangable) are:

    * `OpenCV 2.0 <http://sourceforge.net/projects/opencvlibrary/>`_: Camera input.
    * `PIL <http://www.pythonware.com/products/pil/index.htm>`_: Image and text display.
    * `PyCairo <http://www.cairographics.org/pycairo/>`_: Text display.
    * `PyEnchant <http://www.rfk.id.au/software/pyenchant/>`_: Spelling correction.
    * `Pygame <http://www.pygame.org>`_ : Window creation, image and text display, audio playback.
    * `PyGST <http://gstreamer.freedesktop.org/ + http://pygstdocs.berlios.de/>`_: Audio/video playback and camera input.


Stable version
--------------

No stable version yet.

Development version
-------------------

If you want to work with the latest version of Kivy, you must clone and use our source code repository from `Github <https://github.com/tito/kivy/>`_.

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



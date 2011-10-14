Unit tests
==========

Unit tests are seperated in two cases:

* Non graphics unit tests: theses are standard unit tests that can run in console
* Graphics unit tests: theses need a GL context, and work with image comparaison

To be able to run unit test, you need to install nose
(http://code.google.com/p/python-nose/), and coverage
(http://nedbatchelder.com/code/coverage/). You can use easy_install for that::

    sudo easy_install nose coverage

Then, in the kivy directory::

    make test

How it's working
----------------

All the tests are located in `kivy/tests`, and the filename start with
`test_<name>.py`. Nose will automatically get all theses files and class
inside it, and use it as a test case.

To write a test, create a file that respect the previous naming, then you can
start with that template::

    import unittest

    class XXXTestCase(unittest.TestCase):

        def setUp(self):
            # import class and prepare everything here.
            pass

        def test_YYY(self):
            # place your test case here
            a = 1
            self.assertEqual(a, 1)

Replace `XXX` with an appropriate name that cover your tests cases, then
replace YYY by the name of your test. If you have some doubt, check how others
files are done.

Then, to execute them, just run::

    make test

If you want to execute that file only, you can run::

    nosetests kivy/tests/test_yourtestcase.py


GL unit tests
-------------

GL unit test are more difficult. You must know that even if OpenGL is a
standard, the output/rendering is not. It depends on your GPU and the driver
used. For theses tests, the goal is to save the output of the rendering at
frame X, and compare it to a reference image.

Currently, images are generated in 320x240, png.

.. note::

    Currently, the image comparaison is done per pixel. That mean the reference
    image that you will generate will be only correct for your GPU/driver. If
    somebody can implement a image comparaison with "delta" support, patches
    welcome :)

To execute gl unit test, you need to create a directory::

    mkdir kivy/tests/results
    make test

The results directory will contain all the reference images, and the current
generated images. At the first execution, if the results directory is empty, no
comparaison will be done. It will use the generated images as reference.
The second time, all the images will be compared to the reference image.

A html file is available to show the comparaison before/after the test, and a
snippet of the associated unit test. It will be generated at:

    kivy/tests/build/index.html

.. note::

    The build directory is cleaned after each call to `make test`. If you don't
    want that, just use nosetests command.

Writing GL Unit tests
---------------------

The idea is to create a root widget, as you would do in
:meth:`~kivy.app.App.build()`, or for :func:`kivy.base.runTouchApp()`.
You'll give that root widget to a rendering function, that will capture the
output in X frames.

Here is an example::

    from common import GraphicUnitTest

    class VertexInstructionTestCase(GraphicUnitTest):

        def test_ellipse(self):
            from kivy.uix.widget import Widget
            from kivy.graphics import Ellipse, Color
            r = self.render

            # create a root widget
            wid = Widget()

            # put some graphics instruction on it
            with wid.canvas:
                Color(1, 1, 1)
                self.e = Ellipse(pos=(100, 100), size=(200, 100))

            # render, and capture it directly
            r(wid)

            # as alternative, you can capture in 2 frames:
            r(wid, 2)

            # or in 10 frames
            r(wid, 10)

Each call to `self.render` (or `r` in our example) will generate image named
like this::

    <classname>_<funcname>-<r-call-count>.png

`r-call-count` represent the number of time that `self.render` is called inside
the test function.

The reference images are named::

    ref_<classname>_<funcname>-<r-call-count>.png

You can replace the reference image with a new one easilly.


Coverage reports
----------------

Coverage are based on the execution of the previous tests. Statistics on code
coverage are automatically grabbed during execution. You can generate an html
report of the coverage with the command::

    make cover

Then, open `kivy/htmlcov/index.html` with your favorite web browser.

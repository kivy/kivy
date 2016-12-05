Unit tests
==========

Tests are located in the kivy/tests folder. If you find a bug in Kivy, a good
thing to do can be to write a minimal case showing the issue and to ask core
devs if the behaviour shown is intended or a real bug. If you write your code
as a `unittest <http://docs.python.org/2/library/unittest.html>`_
, it will prevent the bug from coming back unnoticed in the future,
and will make Kivy a better, stronger project. Writing a unittest may be a
really good way to get familiar with Kivy while doing something useful.

Unit tests are separated into two cases:

* Non graphical unit tests: these are standard unit tests that can run in a
  console
* Graphical unit tests: these need a GL context, and work via image comparison

To be able to run unit tests, you need to install nose
(http://code.google.com/p/python-nose/), and coverage
(http://nedbatchelder.com/code/coverage/). You can use easy_install for that::

    sudo easy_install nose coverage

Then, in the kivy directory::

    make test

How it works
------------

All the tests are located in `kivy/tests`, and the filename starts with
`test_<name>.py`. Nose will automatically gather all the files and classes
inside this folder, and use them to generate test cases.

To write a test, create a file that respects the previous naming, then
start with this template::

    import unittest

    class XXXTestCase(unittest.TestCase):

        def setUp(self):
            # import class and prepare everything here.
            pass

        def test_YYY(self):
            # place your test case here
            a = 1
            self.assertEqual(a, 1)

Replace `XXX` with an appropriate name that covers your tests cases, then
replace 'YYY' with the name of your test. If you have any doubts, check how
the other tests have been written.

Then, to execute them, just run::

    make test

If you want to execute that file only, you can run::

    nosetests kivy/tests/test_yourtestcase.py


GL unit tests
-------------

GL unit test are more difficult. You must know that even if OpenGL is a
standard, the output/rendering is not. It depends on your GPU and the driver
used. For these tests, the goal is to save the output of the rendering at
frame X, and compare it to a reference image.

Currently, images are generated at 320x240 pixels, in *png* format.

.. note::

    Currently, image comparison is done per-pixel. This means the reference
    image that you generate will only be correct for your GPU/driver. If
    somebody can implement image comparison with "delta" support, patches
    are welcome :)

To execute GL unit tests, you need to create a directory::

    mkdir kivy/tests/results
    make test

The results directory will contain all the reference images and the
generated images. After the first execution, if the results directory is empty,
no comparison will be done. It will use the generated images as reference.
After the second execution, all the images will be compared to the reference
images.

A html file is available to show the comparison before/after the test, and a
snippet of the associated unit test. It will be generated at:

    kivy/tests/build/index.html

.. note::

    The build directory is cleaned after each call to `make test`. If you don't
    want that, just use nosetests command.

Writing GL Unit tests
---------------------

The idea is to create a root widget, as you would do in
:meth:`~kivy.app.App.build`, or in :func:`kivy.base.runTouchApp`.
You'll give that root widget to a rendering function which will capture the
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

Each call to `self.render` (or `r` in our example) will generate an image named
as follows::

    <classname>_<funcname>-<r-call-count>.png

`r-call-count` represents the number of times that `self.render` is called
inside the test function.

The reference images are named::

    ref_<classname>_<funcname>-<r-call-count>.png

You can easily replace the reference image with a new one if you wish.


Coverage reports
----------------

Coverage is based on the execution of previous tests. Statistics on code
coverage are automatically calculated during execution. You can generate an html
report of the coverage with the command::

    make cover

Then, open `kivy/htmlcov/index.html` with your favorite web browser.

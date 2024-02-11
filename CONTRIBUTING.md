# Contribution Guidelines

Kivy is a large product used by many thousands of developers for free, but it 
is built entirely by the contributions of volunteers. We welcome (and rely on) 
users who want to give back to the community by contributing to the project.

Contributions can come in many forms. This 
chapter discusses how you can help us.

Except where specified, this chapter applies to the entire Kivy ecosystem: the
Kivy framework and all the sibling projects. However, check the documentation 
of individual projects - some have special instructions (including, for example,
python-for-android).

## Ways you can help out

* The most direct way is submitting source code changes: bug-fixes, new code 
and documentation amendments to improve the products. See [Code 
Contributions](#code-contributions) and [Documentation 
Contributions](#documentation-contributions) below for   detailed instructions.
  
* Submitting bug reports and new feature suggestions in our Issue trackers is
  also welcome.

  If you are asking "Why did I get this error?" or "How do I implement this?"
  please **don't** raise an issue yet. Take it to our support channels instead
  (see [Contact Us](CONTACT.md)); until we   can be fairly confident it is a bug
  in the Kivy ecosystem, it isn't ready to be raised as an issue. That said,
  we *do* want to hear about even the most minor typos or problems you find.

  See [Reporting An Issue](#reporting-an-issue) below for detailed instructions.

* You could help out by looking at the issues that other people have raised.

  * Tell us whether you can reproduce the error (on similar and/or different
    platforms). If the problem has already been fixed and no-one noticed, let 
    us know!

  * If the submitter was unclear, shed whatever light you can. Submitting a 
    short piece of code that demonstrates the problem is incredibly helpful.
    Providing details logs can give others the clues that they need.

  * Got some coding skills?

    * If you are new to Kivy, consider looking at the `Easy` or 
      `Good First Issue` tags on each project while you learn the process.

    * Try some debugging? Even if you can't propose a solution, pointing out
      where the current code (or documentation) is wrong can be the difference
      between an issue floundering and getting quickly solved.

    * If you are a little more experienced, then take a look for issues where
      someone has proposed a detailed solution without submitting a PR. That's 
      a great opportunity for a quick win.

    * Want to be a real hero? Become a foster parent for an old open PR, where
      the submitter has bitten off more than they can chew. It will need you to
      understand the problem they were solving, and understand how they were
      trying to solve it. You'll need to review it, and fix problems yourself.
      You will need to rebase it, so it can be merged. Then submit it again,
      and advocate for it until it is merged.

  * You know what is even rarer than coding skills on an open source project?
    Writing skills! If you can write clearly, there are plenty of documentation
    improvements that have been identified.

    * Can you identify a common question from support? Add the answer to the
      appropriate project's FAQ (e.g. [the Kivy Framework FAQ](FAQ.md)) and 
      save people time.

* You don't need to find a bug or come up with a new idea to contribute to the
  code base.

  * Review some code. See if you can spot flaws before they become bugs.

  * Refactor some code. Make it easier for the next person to understand and
    modify.

  * Add some unit-tests. It can be difficult to persuade occasional
    contributors to include sufficient unit tests. A solid bank of unit-tests
    makes further development much faster - your small effort can have
    long-term benefits. See 
    [Kivy Framework Unit Tests](#kivy-framework-unit-tests) for
    more about how our unit-tests are structured. Don't be afraid to refactor if
    the original code is hard to test.

* Kivy is extensible. You can add a new Widget or a new Python-For-Android
  recipe, and have your code re-used by the community.
  [Kivy Garden](https://kivy-garden.github.io/) is an independent project to
  publish and promote third-party Widgets for Kivy.

* Outside the code and documentation, there are still so many ways to help.

  * Monitor the Discussions and Support Channels, and help beginners out.

  * Evangelise: Tell people about Kivy and what you are using it for. Give a
    talk about Kivy.

  * Submit your project to the Kivy gallery to show people what it can do.

    * Even if you don't want it showcased, tell us what you've done! It is very
      motivational to see others using your code successfully.

  * Persuade your organization to become a 
    [sponsor](https://opencollective.com/kivy).

There is no shortage of ways you can help The Open Source community is built on
volunteers contributing what they can when they can. Even if you aren't an
experienced coder, you can make those that are more productive.


## Planning

If you want to discuss your contributions before you make them,
to get feedback and advice, you can ask us on the `#dev` channel of our
[Discord server](https://chat.kivy.org).

The GitHub issue trackers are a more formal tracking mechanism, and
offer lots of opportunities to help out in ways that aren't just
submitting new code.

## Code of Conduct

We have adopted a Code of Conduct in the interest of fostering an open and
welcoming community. See our [Code of Conduct](CODE_OF_CONDUCT.md) for the
details.

## Reporting an Issue

If you found anything wrong - a bug in Kivy, missing documentation, incorrect 
spelling or just unclear examples -  please take two minutes to report the 
issue. If you are unsure, please try our support channels first; see 
[Contact Us](CONTACT.md) for details.

If you can produce a small example of a program that fails, it helps immensely:

1. Move your logging level to debug by editing 
   `<user_directory>/.kivy/config.ini`:

       [kivy]
       log_level = debug

2. Execute your code again, and copy/paste the complete output to 
   [GitHub's gist](http://gist.github.com/), including the log from Kivy and
   the Python backtrace.

To raise the issue:

1. Open the GitHub issue database appropriate for the project - e.g.
[Kivy Framework](https://github.com/kivy/kivy/issues/),
[Buildozer](https://github.com/kivy/buildozer/issues/),
[python-for-android](https://github.com/kivy/python-for-android/issues/),
[kivy-ios](https://github.com/kivy/kivy-ios/issues/),
etc.
2. Set the title of your issue - use it to describe the problem succintly.
3. Explain exactly what to do to reproduce the issue and paste the link of the
   output posted on [GitHub's gist](http://gist.github.com/).
4. Use the Preview tab to check how it looks - if you've pasted logs straight in
at can cause formatting chaos. 
5. Submit it and you're done!

## Code Contributions

Code contributions (patches, new features) are the most obvious way to help with
the project's development. Since this is so common we ask you to follow our
workflow to most efficiently work with us. Adhering to our workflow ensures that
your contribution won't be forgotten or lost. Also, your name will always be
associated with the change you made, which basically means eternal fame in our
code history (you can opt out if you don't want that).

### Coding style

- If you haven't done it yet, read
  [PEP8](http://www.python.org/dev/peps/pep-0008/) about coding style in Python.

- If you  are working on the Kivy Framework, you can automate style checks on
  GitHub commit:

  If are developing on Unix or OSX or otherwise have `make` installed, change
  to the Kivy source directory, and simply run:

      make hook

  This will pass the code added to the git staging zone (about to be committed)
  through a checker program when you do a commit, and ensure that you didn't
  introduce style errors. If you did, the commit will be rejected: please correct the
  errors and try again.

  The checker used is [pre-commit](https://pre-commit.com/). If you need to 
  skip a particular check see its 
  [documentation](https://pre-commit.com/#temporarily-disabling-hooks),
  but, in summmary, on Linux, putting `SKIP=hookname` in front of `git commit` 
  will skip that hook. The name of the offending hook is shown when it fails.

### Performance

- Take care of performance issues: read
  [Python performance tips](http://wiki.python.org/moin/PythonSpeed/PerformanceTips).
- CPU-intensive parts of Kivy are written in Cython: if you are doing a lot of
  computation, consider using it too.

### Git & GitHub

We use git as our version control system for our code base. If you have never
used git or a similar DVCS (or even any VCS) before, we strongly suggest you
take a look at the great documentation that is available for git online.
The [Git Community Book](http://book.git-scm.com/) or the
[Git Videos](https://git-scm.com/videos) are both great ways to learn git.
Trust us when we say that git is a great tool. It may seem daunting at first,
but after a while you'll (hopefully) love it as much as we do. Teaching you git,
however, is well beyond the scope of this document.

Also, we use [GitHub](http://github.com) to host our code. In the following we
will assume that you have a (free) GitHub account. While this part is optional,
it allows for a tight integration between your patches and our upstream code
base. If you don't want to use GitHub, we assume you know what you are doing anyway.

### Code Workflow

These instructions are written from the perspective of the Kivy framework, but their
equivalents apply to other Kivy sibling projects.

The initial setup to begin with our workflow only needs to be done once.
Follow the regular installation instructions but don't clone the repository.
Instead, make a fork. Here are the steps:

1. Log in to GitHub
2. Create a fork of the appropriate repository (e.g.
   [Kivy framework repository](https://github.com/kivy/kivy)) by
   clicking the *fork* button.
3. Clone your fork of our repository to your computer. Your fork will have
   the git remote name 'origin' and you will be on branch 'master'::

        git clone https://github.com/username/kivy.git

   (Replace `kivy` if it isn't the Kivy framework repository.)

4. Compile and set up PYTHONPATH or install.
5. Add the kivy repo as a remote source::

        git remote add kivy https://github.com/kivy/kivy.git

    (Replace `kivy` and URL if it isn't the Kivy framework repository.)

Now, whenever you want to create a patch, you follow the following steps:

1. See if there is a ticket in our bug tracker for the fix or feature and
    announce that you'll be working on it if it doesn't yet have an assignee.
2. Create a new, appropriately named branch in your local repository for
    that specific feature or bugfix.
    (Keeping a new branch per feature makes sure we can easily pull in your
    changes without pulling any other stuff that is not supposed to be pulled.)::

        git checkout -b new_feature

3. Modify the code to do what you want (e.g. fix it).
4. Test the code. Add automated unit-tests to show it works. Do this even for
   small fixes. You never know whether you have introduced some weird bug
   without testing.
5. Do one or more minimal, atomic commits per fix or per feature.
   Minimal/Atomic means *keep the commit clean*. Don't commit other stuff that
   doesn't logically belong to this fix or feature. This is **not** about
   creating one commit per line changed. Use ``git add -p`` if necessary.
6. Give each commit an appropriate commit message, so that others who are
   not familiar with the matter get a good idea of what you changed.
7. Once you are satisfied with your changes, pull our upstream repository and
   merge it with you local repository. We can pull your stuff, but since you know
   exactly what's changed, you should do the merge::

        git pull kivy master

8. Push your local branch into your remote repository on GitHub::

        git push origin new_feature

9. Send a *Pull Request* with a description of what you changed via the button
   in the GitHub interface of your repository. (This is why we forked
   initially. Your repository is linked against ours.)

Warning:  If you change parts of the code base that require compilation, you
        will have to recompile in order for your changes to take effect. The ``make``
        command will do that for you (see the Makefile if you want to know
        what it does). If you need to clean your current directory from compiled
        files, execute ``make clean``. If you want to get rid of **all** files that are
        not under version control, run ``make distclean``
        (**Caution:** If your changes are not under version control, this
        command will delete them!)

Now we will receive your pull request. We will check whether your changes are
clean and make sense (if you talked to us before doing all of this we will have
told you whether it makes sense or not). If so, we will pull them, and you will
get instant karma. Congratulations, you're a hero!

## Documentation Contributions

Documentation contributions generally follow the same workflow as code contributions,
but are just a bit more lax.

1. Follow the instructions above

   1. Fork the repository.
   2. Clone your fork to your computer.
   3. Setup kivy repo as a remote source.

2. Install python-sphinx. (See [doc/README](doc/README) for assistance.)

3. Use [ReStructuredText Markup](http://docutils.sourceforge.net/rst.html) to 
   make changes to the HTML documentation in docs/sources.

To submit a documentation update, use the following steps:

1. Create a new, appropriately named branch in your local repository::

        git checkout -b my_docs_update

2. Modify the documentation with your correction or improvement.
3. Re-generate the HTML pages, and review your update::

        make html

4. Give each commit an appropriate commit message, so that others who are not familiar with
   the matter get a good idea of what you changed.
5. Keep each commit focused on a single related theme. Don't commit other stuff that doesn't
   logically belong to this update.

6. Push to your remote repository on GitHub::

        git push

7. Send a *Pull Request* with a description of what you changed via the button in the
       GitHub interface of your repository.

We don't ask you to go through all the hassle just to correct a single typo, but for more
complex contributions, please follow the suggested workflow.

### Docstrings

Every module/class/method/function needs a docstring, so use the following keywords
when relevant:

- `.. versionadded::` to mark the version in which the feature was added.
- `.. versionchanged::` to mark the version in which the behaviour of the feature was
  changed.
- `.. note::` to add additional info about how to use the feature or related
  feature.
- `.. warning::` to indicate a potential issue the user might run into using
  the feature.
- `.. deprecated::` to indicate when a feature started being deprecated.

Examples::

    def my_new_feature(self, arg):
        """
        New feature is awesome

        .. versionadded:: 1.1.4

        .. note:: This new feature will likely blow your mind

        .. warning:: Please take a seat before trying this feature
        """

When referring to other parts of the api use:

- ``:mod:`~kivy.module``` to refer to a module
- ``:class:`~kivy.module.Class``` to refer to a class
- ``:meth:`~kivy.module.Class.method``` to refer to a method
- ``:doc:`api-kivy.module``` to refer to the documentation of a module (same
  for a class and a method)

Replace `module`, `class` and `method` with their real names, and
use '.' to separate submodule names, e.g::

    :mod:`~kivy.uix.floatlayout`
    :class:`~kivy.uix.floatlayout.FloatLayout`
    :meth:`~kivy.core.window.WindowBase.toggle_fullscreen`
    :doc:`/api-kivy.core.window`

The markers `:doc:` and `:mod:` are essentially the same, except for an anchor 
in the url which makes `:doc:` preferred for the cleaner url.

To build your documentation, run::

    make html

If you updated your kivy install, and have some trouble compiling docs, run::

    make clean force html

The docs will be generated in `docs/build/html`. For more information on
docstring formatting, please refer to the official
[Sphinx Documentation](http://sphinx-doc.org/).

## Kivy Framework Unit Tests

These instructions are specific to the Kivy framework (i.e. kivy/kivy in GitHub).

Tests are located in the `kivy/tests` folder. If you find a bug in Kivy, a good
thing to do is to write a minimal case showing the issue and to ask on the 
support chnnels if the behaviour shown is intended or a real bug. If you 
contribute your code as a 
[unittest](https://docs.python.org/3/library/unittest.html), it will prevent the 
bug from coming back unnoticed in the future (a "regression"), and will
make Kivy a better, stronger project. Writing a unittest is a great
way to get familiar with Kivy's code while contributing something useful.

Unit tests are separated into two cases:

* Non-graphical unit tests: these are standard unit tests that can run in a
  console
* Graphical unit tests: these need a GL context, and if requested, work via
  image comparison

To be able to run unit tests, you need to install [pytest](https://pytest.org/),
and [coverage](http://nedbatchelder.com/code/coverage/). You can use pip for
that::

    sudo pip install kivy[dev]

Then, in the kivy directory::

    make test

### How it works

All the tests are located in `kivy/tests`, and the filename starts with
`test_<name>.py`. Pytest will automatically gather all the files and classes
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
replace `YYY` with the name of your test. If you have any doubts, check how
the other tests have been written.

Then, to execute them, just run::

    make test

If you want to execute that file only, you can run::

    pytest kivy/tests/test_yourtestcase.py

or include this simple `unittest.main()` call at the end of the file and run
the test with `python test_yourtestcase.py`::

    if __name__ == '__main__':
        unittest.main()


### Graphical unit tests

While simple unit tests are fine and useful to keep things granular, in certain
cases we need to test Kivy after the GL Window is created to interact with the
graphics, widgets and to test more advanced stuff such as widget, modules,
various cases of input and interaction with everything that becomes available
only after the Window is created and Kivy properly initialized.

These tests are executed the same way as the ordinary unit tests i.e. either
with `pytest` or via `unittest.main()`.

Here are two similar examples with different approaches of running the app.
In the first one you are setting up the required stuff manually and the
`tearDown()` of the `GraphicUnitTest` will attempt to clean it after you::

    from kivy.tests.common import GraphicUnitTest

    class MyTestCase(GraphicUnitTest):

        def test_runtouchapp(self):
            # non-integrated approach
            from kivy.app import runTouchApp
            from kivy.uix.button import Button

            button = Button()
            runTouchApp(button)

            # get your Window instance safely
            from kivy.base import EventLoop
            EventLoop.ensure_window()
            window = EventLoop.window

            # your asserts
            self.assertEqual(window.children[0], button)
            self.assertEqual(
                window.children[0].height,
                window.height
            )

In the second test case both `setUp()` and `tearDown()` work together with
`GraphicUnitTest.render()`. This is the basic setup it does automatically:

* Window is sized to 320 x 240 px
* Only the default Config is used during the test, it's restricted with the
  `KIVY_USE_DEFAULTCONFIG` environment variable
* Any input (mouse/touch/...) is *removed* and if you need to test it, either
  mock it or manually add it
* Window's canvas is cleared before displaying any widget tree

Warning: Do NOT use absolute numbers in your tests to preserve the functionality
across the all resolutions. Instead, use e.g. relative position or size and
multiply it by the `Window.size` in your test.



    from kivy.tests.common import GraphicUnitTest, UnitTestTouch

    class MyTestCase(GraphicUnitTest):

        def test_render(self):
            from kivy.uix.button import Button

            # with GraphicUnitTest.render() you basically do this:
            # runTouchApp(Button()) + some setup before
            button = Button()
            self.render(button)

            # get your Window instance safely
            from kivy.base import EventLoop
            EventLoop.ensure_window()
            window = EventLoop.window

            touch = UnitTestTouch(
                *[s / 2.0 for s in window.size]
            )

            # bind something to test the touch with
            button.bind(
                on_release=lambda instance: setattr(
                    instance, 'test_released', True
                )
            )

            # then let's touch the Window's center
            touch.touch_down()
            touch.touch_up()
            self.assertTrue(button.test_released)


    if __name__ == '__main__':
        import unittest
        unittest.main()

Note: Make sure you check the source of `kivy.tests.common` before writing
comprehensive test cases.


### GL unit tests

GL unit test are more difficult. You must know that even if OpenGL is a
standard, the output/rendering is not. It depends on your GPU and the driver
used. For these tests, the goal is to save the output of the rendering at
frame X, and compare it to a reference image.

Currently, images are generated at 320x240 pixels, in *png* format.

Note: Currently, image comparison is done per-pixel. This means the reference
    image that you generate will only be correct for your GPU/driver. If
    somebody can implement image comparison with "delta" support, patches
    are welcome :)

To execute GL unit tests, you need to create a directory::

    mkdir kivy/tests/results
    KIVY_UNITTEST_SCREENSHOTS=1 make test

The results directory will contain all the reference images and the
generated images. After the first execution, if the results directory is empty,
no comparison will be done. It will use the generated images as reference.
After the second execution, all the images will be compared to the reference
images.

A html file is available to show the comparison before/after the test, and a
snippet of the associated unit test. It will be generated at:

    kivy/tests/build/index.html

Note: The build directory is cleaned after each call to `make test`. If you don't
    want that, just use pytest command.

#### Writing GL Unit tests


The idea is to create a root widget, as you would do in
`kivy.app.App.build`, or in `kivy.base.runTouchApp`.
You'll give that root widget to a rendering function which will capture the
output in X Window frames.

Here is an example::

    from kivy.tests.common import GraphicUnitTest

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

### Coverage reports

Coverage is based on the execution of previous tests. Statistics on code
coverage are automatically calculated during execution. You can generate an HTML
report of the coverage with the command::

    make cover

Then, open `kivy/htmlcov/index.html` with your favorite web browser.

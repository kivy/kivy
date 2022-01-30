.. _faq:

FAQ
===

There are a number of questions that repeatedly need to be answered.
The following document tries to answer some of them.



Technical FAQ
-------------

Unable to get a Window, abort.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Kivy cannot instantiate a Window core provider (mostly SDL2), you'll see
this. The underlying issue depends on many things:

- Check your installation. Twice.
- Check that your graphics driver support OpenGL 2.1 at the minimum. Otherwise, Kivy can't run.
- If you use windows and ANGLE (``KIVY_GL_BACKEND=angle_sdl2``), check that you have DirectX 9 support.
- If your platform doesn't supports OpenGL, SDL2 cannot initialize OpenGL.
- Don't mix the architecture of the dependencies (e.g. Python 64-bit and 32-bit extensions/SDL2)
- Don't mix python installation: e.g. if you have Python and Anaconda installed, the Python actually run may be different than you think. Similarly, if you have multiple Python versions available on the ``PATH``, they may clash.
- Check your PATH to ensure that other programs in it don't provide the same dlls as Kivy/Python, or bad stuff can happen.

  - This commonly happens if some other program that uses similar dependencies as Kivy adds itself to the ``PATH`` so that Kivy's dependencies clash with theirs.
  - Please read `this <https://superuser.com/questions/284342/what-are-path-and-other-environment-variables-and-how-can-i-set-or-use-them>`_ and `this <https://www.digitalcitizen.life/simple-questions-what-are-environment-variables>`_ for more details on ``PATH``.
  - The best tool to troubleshoot this is with `Dependency Walker <http://www.dependencywalker.com/>`_ explained `here <https://www.thewindowsclub.com/dependency-walker-download>`_ and `here <https://kb.froglogic.com/display/KB/Analyzing+dependencies+with+Dependency+Walker>`_.
  - But ensure that you're launching it from the identical environment that you start Python.
- Ensure you have all dependencies installed (like ``kivy_deps.sdl2``).
- Maybe your drivers have some missing OpenGL symbols? Try to switch to another graphics backend with ``KIVY_GL_BACKEND``.
- Maybe your `Pycharm configuration is incorrect <https://stackoverflow.com/questions/49466785/kivy-error-python-2-7-sdl2-import-error>`_.


Fatal Python error: (pygame parachute) Segmentation Fault
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of time, this issue is due to the usage of old graphics drivers. Install the
latest graphics driver available for your graphics card, and it should be ok.

If not, this means you have probably triggered some OpenGL code without an
available OpenGL context. If you are loading images, atlases, using graphics
instructions, you must spawn a Window first::

    # method 1 (preferred)
    from kivy.base import EventLoop
    EventLoop.ensure_window()

    # method 2
    from kivy.core.window import Window

If not, please report a detailed issue on github by following the instructions
in the :ref:`reporting_issues` section of the :doc:`contribute` documentation.
This is very important for us because that kind of error can be very hard
to debug. Give us all the information you can give about your environment and
execution.


undefined symbol: glGenerateMipmap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You graphics card or its drivers might be too old. Update your graphics drivers to the
latest available version and retry.

ImportError: No module named event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you use Kivy from our development version, you must compile it before
using it. In the kivy directory, do::

    make force


Android FAQ
-----------

Crash on touch interaction on Android 2.3.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There have been reports of crashes on Adreno 200/205 based devices.
Apps otherwise run fine but crash when interacted with/through the screen.

These reports also mentioned the issue being resolved when moving to an ICS or
higher ROM.

Is it possible to have a kiosk app on android 3.0 ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Thomas Hansen have wrote a detailed answer on the kivy-users mailing list:

    https://groups.google.com/d/msg/kivy-users/QKoCekAR1c0/yV-85Y_iAwoJ

Basically, you need to root the device, remove the SystemUI package, add some
lines to the xml configuration, and you're done.

What's the difference between python-for-android from Kivy and SL4A?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Despite having the same name, Kivy's python-for-android is not related to the
python-for-android project from SL4A, Py4A, or android-python27. They are
distinctly different projects with different goals. You may be able to use
Py4A with Kivy, but no code or effort has been made to do so. The Kivy team
feels that our python-for-android is the best solution for us going forward,
and attempts to integrate with and support Py4A is not a good use of our time.


Project FAQ
-----------

Why do you use Python? Isn't it slow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let us try to give a thorough answer; please bear with us.

Python is a very agile language that allows you to do many things
in a (by comparison) short time.
For many development scenarios, we strongly prefer writing our
application quickly in a high-level language such as Python, testing
it, then optionally optimizing it.

But what about speed?
If you compare execution speeds of implementations for a certain set of
algorithms (esp. number crunching) you will find that Python is a lot
slower than say, C++.
Now you may be even more convinced that it's not a good idea in our
case to use Python. Drawing sophisticated graphics (and we are
not talking about your grandmother's OpenGL here) is computationally
quite expensive and given that we often want to do that for rich user
experiences, that would be a fair argument.
**But**, in virtually every case your application ends up spending
most of the time (by far) executing the same part of the code.
In Kivy, for example, these parts are event dispatching and graphics
drawing. Now Python allows you to do something to make these parts
much faster.

By using Cython, you can compile your code down to the C level,
and from there your usual C compiler optimizes things. This is
a pretty pain free process and if you add some hints to your
code, the result becomes even faster. We are talking about a speed up
in performance by a factor of anything between 1x and up to more
than 1000x (greatly depends on your code). In Kivy, we did this for
you and implemented the portions of our code, where efficiency really
is critical, on the C level.

For graphics drawing, we also leverage today's GPUs which are, for
some tasks such as graphics rasterization, much more efficient than a
CPU. Kivy does as much as is reasonable on the GPU to maximize
performance. If you use our Canvas API to do the drawing, there is
even a compiler that we invented which optimizes your drawing code
automatically. If you keep your drawing mostly on the GPU,
much of your program's execution speed is not determined by the
programming language used, but by the graphics hardware you throw at
it.

We believe that these (and other) optimizations that Kivy does for you
already make most applications fast enough by far. Often you will even
want to limit the speed of the application in order not to waste
resources.
But even if this is not sufficient, you still have the option of using
Cython for your own code to *greatly* speed it up.

Trust us when we say that we have given this very careful thought.
We have performed many different benchmarks and come up with some
clever optimizations to make your application run smoothly.


Does Kivy support Python 3.x?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Kivy |kivy_version_bold| officially supports Python versions |python_versions_bold|.

As of version **2.0.0** Kivy dropped support for Python 2. You can still use older versions with
Python 2 support. 

Python 3 is also supported by python-for-android and kivy-ios.


How is Kivy related to PyMT?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our developers are professionals and are pretty savvy in their
area of expertise. However, before Kivy came around there was (and
still is) a project named PyMT that was led by our core developers.
We learned a great deal from that project during the time that we
developed it. In the more than two years of research and development
we found many interesting ways to improve the design of our
framework. We have performed numerous benchmarks and as it turns out,
to achieve the great speed and flexibility that Kivy has, we had to
rewrite quite a big portion of the codebase, making this a
backwards-incompatible but future-proof decision.
Most notable are the performance increases, which are just incredible.
Kivy starts and operates just so much faster, due to these heavy
optimizations.
We also had the opportunity to work with businesses and associations
using PyMT. We were able to test our product on a large diversity of
setups and made PyMT work on all of them. Writing a system such as
Kivy or PyMT is one thing. Making it work under all these different
conditions is another. We have a good background here, and brought our
knowledge to Kivy.

Furthermore, since some of our core developers decided to drop their full-time
jobs and turn to this project completely, it was decided that a more
professional foundation had to be laid. Kivy is that foundation. It is
supposed to be a stable and professional product.
Technically, Kivy is not really a successor to PyMT because there is
no easy migration path between them. However, the goal is the same:
Producing high-quality applications for novel user interfaces.
This is why we encourage everyone to base new projects on Kivy instead
of PyMT.
Active development of PyMT has stalled. Maintenance patches are still
accepted.


Do you accept patches?
~~~~~~~~~~~~~~~~~~~~~~

Yes, we love patches. In order to ensure a smooth integration of your
precious changes however, please make sure to read our contribution
guidelines.
Obviously we don't accept every patch. Your patch has to be consistent
with our styleguide and, more importantly, make sense.
It does make sense to talk to us before you come up with bigger
changes, especially new features.


Does the Kivy project participate in Google's Summer of Code ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Potential students ask whether we participate in GSoC.
The clear answer is: Indeed. :-)

If you want to participate as a student and want to maximize your
chances of being accepted, start talking to us today and try fixing
some smaller (or larger, if you can ;-) problems to get used to our
workflow. If we know you can work well with us, that'd be a big plus.

Here's a checklist:

* Make sure to read through the website and at least skim the documentation.
* Look at the source code.
* Read our contribution guidelines.
* Pick an idea that you think is interesting from the ideas list (see link
  above) or come up with your own idea.
* Do some research **yourself**. GSoC is not about us teaching you something
  and you getting paid for that. It is about you trying to achieve agreed upon
  goals by yourself with our support. The main driving force in this should be,
  obviously, yourself.  Many students come up and ask what they should
  do. Well, we don't know because we know neither your interests nor your
  skills. Show us you're serious about it and take initiative.
* Write a draft proposal about what you want to do. Include what you understand
  the current state is (very roughly), what you would like to improve and how,
  etc.
* Discuss that proposal with us in a timely manner. Get feedback.
* Be patient! Especially on Discord. We will try to get to you if we're available.
  If not, send an email and just wait. Most questions are already answered in
  the docs or somewhere else and can be found with some research. If your
  questions don't reflect that you've actually thought through what you're
  asking, it might not be well received.

Good luck! :-)

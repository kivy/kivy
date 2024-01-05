# FAQ for Kivy Framework

## Introduction
[Kivy](http://kivy.org) is an open-source Python framework for developing 
GUI apps that work cross-platform, including desktop, mobile and embedded 
platforms.

### Sibling Projects with FAQs:

As well as the [Kivy framework](https://github.com/kivy/kivy), there are a
number of sibling projects maintained by the same team. Some have their own FAQs, including: 

* [FAQ](https://github.com/kivy/buildozer/blob/master/FAQ.md) for 
[Buildozer](https://github.com/kivy/buildozer/): a development tool for turning Python applications into binary 
packages ready for installation on any of a number of platforms, including mobile devices.
* [FAQ](https://github.com/kivy/plyer/blob/master/FAQ.md) for [Plyer](https://github.com/kivy/plyer):
a platform-independent Python API for accessing hardware features of various platforms (Android, iOS, macOS, Linux and
Windows).
* [FAQ](https://github.com/kivy/pyjnius/blob/master/FAQ.md) for [PyJNIus](https://github.com/kivy/pyjnius):
a Python library for accessing Java classes using the Java Native Interface (JNI).
* [FAQ](https://github.com/kivy/python-for-android/blob/master/FAQ.md) for 
[python-for-android](https://github.com/kivy/python-for-android):
a development tool that packages Python apps into binaries that can run on Android devices.
* [FAQ](https://github.com/kivy/kivy-ios/blob/master/FAQ.md) for [Kivy for iOS](https://github.com/kivy/kivy-ios):
a toolchain to compile the necessary libraries for iOS to run Kivy applications, and manage the creation of Xcode
projects.

## Project Questions

### Why do you use Python? Isn't it slow?

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
code, the result becomes even faster. We are talking about a speed-up
in performance by a factors like 30 or much more; it greatly depends on your code. 
In Kivy, we did this for
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

### What versions of Python does Kivy support?

Typically, all the versions of Python that [haven't reached End of Life](https://devguide.python.org/versions/).

There may be some delays as new versions of Python are released, while we wait for our dependencies to add support.

To find the answer for the latest released versions, check the Python Package Index (PyPI) for [Kivy](https://pypi.org/project/Kivy/).
If you are developing app for other platforms, check [Buildozer](https://pypi.org/project/buildozer/), 
[python-for-android](https://pypi.org/project/python-for-android/), and [kivy-ios](https://pypi.org/project/kivy-ios/),
as appropriate.

### Do you accept patches?

Yes, we love patches. Obviously we don't accept every patch. Your patch has to be consistent
with our styleguide and, more importantly, make sense. Come talk to us on Discord before you come up with bigger
changes, especially new features.

Make sure to read [our contribution guidelines](FAQ.md).

### Does the Kivy project participate in Google's Summer of Code?

Potential students sometimes ask whether we participate in GSoC.
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

### How does Kivy relate to other projects:

#### Is Kivy related to KivyMD?

[KivyMD](https://kivymd.readthedocs.io/en/1.1.1/) is a separate project to Kivy - 
it is run by a different team. It builds powerful and beautiful widgets for use 
with Kivy. 

#### Is Kivy's python-for-android related to Scripting Layer for Android (SL4A)?

Despite having the same name, Kivy's python-for-android is not related to the
python-for-android project from SL4A, Py4A, or android-python27. They are
distinctly different projects with different goals. You may be able to use
Py4A with Kivy, but no code or effort has been made to do so. The Kivy team
feels that our python-for-android is the best solution for us going forward,
and attempts to integrate with and support Py4A is not a good use of our time.

#### Is Kivy related to PyMT?

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

#### Is Kivy related to kivy3, kivy4 and kivy5?

There is a defunct project in PyPI called `kivy3`. It was developed to 
enhance Kivy to add 3D graphics, but it was not developed by the Kivy team; 
it does not represent the successor to Kivy.

There are projects in PyPI called `kivy4` and `kivy5`. They claim to be 
MIT-licensed projects but do not include source code. They are not produced 
by the Kivy Team, and we would always recommend caution before installing 
binaries from unknown sources.

## Technical Questions

### Can I write apps that support my local language?

The Kivy team is distributed globally and understands the importance of handling
internationalization of software. They are actively working on 
[a number of fronts](https://github.com/kivy/kivy/issues/8444) to make Kivy 
support languages from around the world more seamlessly. It is challenging as 
Kivy is built on a number of technologies and platforms, with differing 
support for display and input of Unicode, Right-to-Left languages, etc.

This guide, [*Supporting Arabic Alphabet in Kivy for Building Cross-Platform Applications*](https://medium.com/@ahmedfgad/supporting-arabic-alphabet-in-kivy-for-building-cross-platform-applications-7a1e7c14a068), 
provides helpful advice in handling many languages, not just Arabic.

For [True Type fonts (TTF)](https://en.wikipedia.org/wiki/TrueType) on platforms
using SDL/SDL2 for graphics, setting a Label's [font_script_name](https://kivy.org/doc/stable/api-kivy.uix.label.html#kivy.uix.label.Label.font_script_name) correctly [can avoid rendering issues](https://github.com/kivy/kivy/issues/7227) with some fonts.

### Should I make a property a Kivy class-level property?

Recall from the [Kivy Properties documentation](https://kivy.org/doc/stable/api-kivy.properties.html#kivy.properties) that the services provided by making something a Kivy Property are:

* Value Checking / Validation: When you assign a new value to a property, the value is checked against validation constraints. For example, validation for an OptionProperty will make sure that the value is in a predefined list of possibilities. Validation for a NumericProperty will check that your value is a numeric type. This prevents many errors early on.
* Observer Pattern: You can specify what should happen when a property’s value changes. You can bind your own function as a callback to changes of a Property. If, for example, you want a piece of code to be called when a widget’s pos property changes, you can bind a function to it.
* Better Memory Management: The same instance of a property is shared across multiple widget instances.

Thus, if you think you will want to use any of those services in conjunction with an attribute, you should probably default to making that attribute a Kivy property. (Occasionally there may be a performance penalty in doing so, but generally speaking, it is advisable to err on the side of using what the Kivy devs have provided, and then later re-factor if such a performance hit becomes noticeable and detrimental. Just remember to avoid using Kivy "keywords," which vary somewhat from class to class, when re-factoring, lest you over-ride something unintentionally.)

### Challenging Error messages 

Here are some error messages that users have found difficult to debug.

#### I get a "Unable to get a Window, abort." error. What do I do?

  If Kivy cannot instantiate a Window core provider (mostly SDL2), you'll see
this. The underlying issue depends on many things:

  - Check your installation. Twice.
  - Check that your graphics driver support OpenGL 2.1 at the minimum. Otherwise, Kivy can't run.
  - If you use windows and ANGLE (`KIVY_GL_BACKEND=angle_sdl2`), check that you have DirectX 9 support.
  - If your platform doesn't support OpenGL, SDL2 cannot initialize OpenGL.
  - Don't mix the architecture of the dependencies (e.g. Python 64-bit and 32-bit extensions/SDL2)
  - Don't mix python installation: e.g. if you have Python and Anaconda installed, the Python actually run may be different than you think. Similarly, if you have multiple Python versions available on the ``PATH``, they may clash.
  - Check your PATH to ensure that other programs in it do not provide the same dlls as Kivy/Python, or bad stuff can happen.
    - This commonly happens if some other program that uses similar dependencies as Kivy adds itself to the `PATH` so that Kivy's dependencies clash with theirs.
    - Please read [this](https://superuser.com/questions/284342/what-are-path-and-other-environment-variables-and-how-can-i-set-or-use-them) and [this](https://www.digitalcitizen.life/simple-questions-what-are-environment-variables) for more details on ``PATH``.
    - The best tool to troubleshoot this is with [Dependency Walker](http://www.dependencywalker.com/) explained [here](https://www.thewindowsclub.com/dependency-walker-download>) and [here](https://kb.froglogic.com/display/KB/Analyzing+dependencies+with+Dependency+Walker).
    - But ensure that you're launching it from the identical environment that you start Python.
  - Ensure you have all dependencies installed (like `kivy_deps.sdl2`).
  - Maybe your drivers have some missing OpenGL symbols? Try to switch to another graphics backend with ``KIVY_GL_BACKEND``.
  - Maybe your [Pycharm configuration is incorrect](https://stackoverflow.com/questions/49466785/kivy-error-python-2-7-sdl2-import-error).

#### I get a "Fatal Python error: (pygame parachute) Segmentation Fault" error. What went wrong?

  Most of time, this issue is due to the usage of old graphics drivers. Install the
latest graphics driver available for your graphics card, and it should be ok.

  If not, this means you have probably triggered some OpenGL code without an
available OpenGL context. If you are loading images, atlases, using graphics
instructions, you must spawn a Window first:

 * method 1 (preferred)

       from kivy.base import EventLoop
       EventLoop.ensure_window()

 * method 2
 
       from kivy.core.window import Window

  If not, please make a bug report. [Instructions are here](https://kivy.org/doc/stable/contribute.html).
That kind of error can be very hard, so please give us all the information you can give about your environment and
execution.

#### I get an "undefined symbol: glGenerateMipmap" error. How do I fix it?

  Your graphics card or its drivers might be too old. Update your graphics drivers to the
latest available version and retry.


#### I get an "ImportError: No module named event". How come?

  If you use Kivy from our development version, you must compile it before
using it. In the kivy directory, run

      make force

## Android Questions

Android-related FAQ issues are documented in the 
[Python-For-Android FAQ](https://github.com/kivy/python-for-android/blob/develop/FAQ.md).

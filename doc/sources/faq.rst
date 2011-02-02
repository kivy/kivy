.. _faq:

Frequently Asked Questions
==========================

There are a number of questions that repeatedly need to be answered.
The following document tries to answer some of them.


Why do you use Python? Isn't it slow?
-------------------------------------

Let us try to give a thorough answer; please bear with us.

Python is a very agile language that allows you to do many things
in (by comparison) short time.
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
For Kivy for example, these parts are event dispatching and graphics
drawing. Now Python allows you to do something to make these parts
much faster.

By using Cython, you can compile your code down to the C level,
and from there your usual C compiler optimizes things. This is
a pretty pain free process and if you add some hints to your
code, the result becomes even faster. We are talking about a speed up
in performance by a factor of anything in between 1x and up to more
than 1000x (greatly depends on your code). In Kivy, we did this for
you and implemented the portions of our code where efficiency really
is critical on the C level.

For graphics drawing, we also leverage today's GPUs which are, for
some tasks such as graphics rasterization, much more efficent than a
CPU. Kivy does as much as is reasonable on the GPU to maximize
performance. If you use our Canvas API to do the drawing, there is
even a compiler that we invented which optimizes your drawing code
automatically. If you keep your drawing on the GPU mostly,
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
We have performed many different benchmarks and came up with quite
some clever optimizations to make your application run smoothly.


Does Kivy support Python 3.x?
-----------------------------

No. Not yet. Python 3 is certainly a good thing; However, it broke
backwards compatibility (for good reasons) which means that some
considerable portion of available Python projects do not yet work
with Python 3. This also applies to some of the projects that Kivy can
use as a dependency, which is why we didn't make the switch yet.
We would also need to switch our own codebase to Python 3. We didn't
do that yet because it's not very high on our priority list, but if
somebody doesn't want to wait for us doing it, please go ahead.
Please note, though, that Python 2.x is still the de facto standard.


How is Kivy related to PyMT?
----------------------------

Our developers are professionals and are pretty savvy in their
area of expertise. However, before Kivy came around there was (and
still is) a project named PyMT that was led by our core developers.
We learned a great deal from that project during the time that we
developed it. In the more than two years of research and development
we found many interesting ways on how to improve the design of our
framework. We have done numerous benchmarks and as it turns out, to
achieve the great speed and flexibility that Kivy has, we had to
rewrite quite a big portion of the codebase, making this a
backwards-incompatible but future-proof decision.
Most notably are the performance increases, which are just incredible.
Kivy starts and operates just so much faster, due to heavy
optimizations.
We also had the opportunity to work with businesses and associations
using PyMT. We were able to test our product on a large diversity of
setups and made PyMT work on all of these. Writing a system such as
Kivy or PyMT is one thing. Making it work under all the different
conditions is another. We have a good background here, and brought our
knowledge to Kivy.

Furthermore, since some of our core developers decided to stop their full-time
jobs and to turn to this project completely, it was decided that a more
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
----------------------

Yes, we love patches. In order to ensure a smooth integration of your
precious changes, however, please make sure to read our contribution
guidelines.
Obviously we don't accept every patch. Your patch has to be coherent
with our styleguide and, more importantly, make sense.
It does make sense to talk to us before you come up with bigger
changes, especially new features.


Does the Kivy project participate in Google's Summer of Code 2011?
------------------------------------------------------------------

Since Google announced that there will be a GSoC 2011 we have had many
potential students ask whether we would participate.
The clear answer is: We don't know, but we hope so.
We will most likely apply and then hopefully get chosen as one of the
mentoring organizations.
If you want to participate as a student and want to maximize your
chances of being accepted, start talking to us today and try fixing
some smaller (or larger, if you can ;-) problems to get used to our
workflow. If we know you can work well with us, that'd be a big plus.


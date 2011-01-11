Frequently Asked Questions
==========================

Does Kivy support Python 3.x?
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
    Yes, we love patches. In order to ensure a smooth integration of your
    precious changes, however, please make sure to read our contribution
    guidelines.
    Obviously we don't accept every patch. Your patch has to be coherent
    with our styleguide and, more importantly, make sense.
    It does make sense to talk to us before you come up with bigger
    changes, especially new features.





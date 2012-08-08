.. _contributing:

Contributing
============

There are many ways in which you can contribute to Kivy.
Code patches are just one thing amongst others that you can submit to help the
project. We also welcome feedback, bug reports, feature requests, documentation
improvements, advertisement & advocating, testing, graphics contributions and
many different things. Just talk to us if you want to help, and we will help you
help us.

Feedback
--------

This is by far the easiest way to contribute something. If you're using
Kivy for your own project, don't hesitate sharing. It doesn't have to be a
high-class enterprise app, obviously. It's just incredibly motivating to
know that people use the things you develop and what it enables them to
do. If you have something that you would like to tell us, please don't
hesitate. Screenshots and videos are also very welcome!
We're also interested in the problems you had when getting started. Please
feel encouraged to report any obstacles you encountered such as missing
documentation, misleading directions or similar.
We are perfectionists, so even if it's just a typo, let us know.

.. _reporting_issues:

Reporting an Issue
------------------

If you found anything wrong, a crash, segfault, missing documentation, invalid
spelling, weird example, please take 2 minutes to report the issue.

#. Move your logging level to debug by editing `<user_directory>/.kivy/config.ini`::

    [kivy]
    log_level = debug

#. Execute again your code, and copy/paste the complete output to http://gist.github.com/,
   including the log from Kivy and the python backtrace.
#. Open https://github.com/kivy/kivy/issues/
#. Write a title of your issue
#. Explain how we can do to reproduce the issue + paste the link of the output previously sent on pocoo
#. Validate the issue, you're done !


If you feel good, you can also try to resolve the bug, and contribute by sending us
the patch :) Read the next section about how to do it.

Code Contributions
------------------

Code contributions (patches, new features) are the most obvious way to help with
the project's development. Since this is so common we ask you to follow our
workflow to most efficiently work with us. Adhering to our workflow ensures that
your contribution won't be forgotten or lost. Also, your name will always be
associated with the change you made, which basically means eternal fame in our
code history (you can opt-out if you don't want that).


Coding style
~~~~~~~~~~~~

- If you didn't do it yet, read the
  `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ about coding style in python.

- Activate pep8 check on git commit like this::

    make hook

This will pass the code added to git staging zone (about to be committed)
thought a pep8 checker program when you do a commit, and check that you didn't
introduce pep8 errors, if so, the commit will be rejected, correct the errors,
and try again.

Performances
~~~~~~~~~~~~

- take care of performance issues, read
  `Python performance tips <http://wiki.python.org/moin/PythonSpeed/PerformanceTips>`_
- cpu intensive parts of Kivy are written in cython, if you are doing a lot of
  computation, consider using it too.

Git & GitHub
~~~~~~~~~~~~

We use git as our version control system for our code base. If you have never
used git or a similar DVCS (or even any VCS) before, we strongly suggest you
take a look at the great documentation that is available for git online.
The `Git Community Book <http://book.git-scm.com/>`_ or the
`Git Screencasts <http://gitcasts.com/>`_ are both great ways to learn git.
Trust us when we say that git is a great tool. It may seem daunting at first,
but after a while you'll (hopefully) love it as much as we do. Teaching you git,
however, is well beyond the scope of this document.

Also, we use `GitHub <http://github.com>`_ to host our code. In the following we
will assume that you have a (free) GitHub account. While this part is optional,
it allows for a tight integration between your patches and our upstream code
base. If you don't want to use GitHub, we assume you know what you do anyway.

Code Workflow
~~~~~~~~~~~~~

So here is the initial setup to begin with our workflow (you only need to do
this once to install Kivy). Basically you follow the installation
instructions from :ref:`dev-install`, but you don't clone our repository,
but the fork you create with the following steps:

    #. Log in to GitHub
    #. Create a fork of the `Kivy repository <https://github.com/kivy/kivy>`_ by
       clicking the *fork* button.
    #. Clone your fork of our repository to your computer. Your fork will have
       the git remote name 'origin' and you will be on branch 'master'.
    #. Compile and set up PYTHONPATH or install (see :ref:`dev-install`).
    #. Install our pre-commit hook that ensures your code doesn't violate our
       styleguide by executing `make hook` from the root directory of your
       clone. This will run our styleguide check whenever you do a commit,
       and if there are violations in the parts that you changed, your commit
       will be aborted. Fix & retry.
    #. Add kivy repo as a remote source::

        git remote add kivy https://github.com/kivy/kivy.git

Now, whenever you want to create a patch, you follow the following steps:

    #. See if there is a ticket in our bug tracker for the fix or feature and
       announce that you'll be working on it if it doesn't yet have an assignee.
    #. Create a new, appropriately named branch in your local repository for
       that specific feature or bugfix.
       (Keeping a new branch per feature makes sure we can easily pull in your
       changes without pulling any other stuff that is not supposed to be pulled.)::

        git checkout -b new_feature

    #. Modify the code to do what you want (e.g., fix it).
    #. Test the code. Try to do this even for small fixes. You never know
       whether you have introduced some weird bug without testing.
    #. Do one or more minimal, atomic commits per fix or per feature.
       Minimal/Atomic means *keep the commit clean*. Don't commit other stuff that
       doesn't logically belong to this fix or feature. This is **not** about
       creating one commit per line changed. Use ``git add -p`` if necessary.
    #. Give each commit an appropriate commit message, so that others who are
       not familiar with the matter get a good idea of what you changed.
    #. Once you are satisfied with your changes, merge with our upstream
       repository. We can pull your stuff, but since you know best what you
       changed, you should do the merge::

        git pull kivy master

    #. Push to your remote repository on GitHub::

        git push

    #. Send a *Pull Request* with a description of what you changed via the button
       in the GitHub interface of your repository. (This is why we forked
       initially. Your repository is linked against ours.)

    .. warning::
        If you change parts of the code base that require compilation, you
        will have to recompile in order for your changes to take effect. The ``make``
        command will do that for you (see the Makefile if you want to know
        what it does). If you need to clean your current directory from compiled
        files, execute ``make clean``. If you want to get rid of **all** files that are
        not under version control, run ``make distclean``
        (**Caution:** If your changes are not under version control, this
        command will delete them!)

Now we will receive your pull request. We will check whether your changes are
clean and make sense (if you talked to us before doing all of this we will have
told you whether it makes sense or not). If so, we will pull them and you will
get instant karma. Congratulations, you're a hero!


Documentation Contributions
---------------------------

Documentation contributions generally follow the same workflow as code
contributions, just a bit more lax. We don't ask you to go through all the
hassle just to correct a single typo. For more complex contributions, please
consider following the suggested workflow though.


Docstrings
~~~~~~~~~~

Every module/class/method/function need a docstring, use the following keyword
when relevant

- ``.. versionadded::`` to mark the version the feature was added.
- ``.. versionchanged::`` to mark the version behaviour of the feature was
  changed.
- ``.. note::`` to add additional info about how to use the feature or related
  feature.
- ``.. warning::`` to indicate a potential issue the user might run into using
  the feature.

Examples::

    def my_new_feature(self, arg):
        """
        New feature is awesome

        .. versionadded:: 1.1.4

        .. note:: This new feature will likely blow your mind

        .. warning:: Please take a seat before trying this feature
        """

Will result in:

    def my_new_feature(self, arg):
        """
        New feature is awesome

        .. versionadded:: 1.1.4

        .. note:: This new feature will likely blow your mind

        .. warning:: Please take a seat before trying this feature

        """


When refering to other parts of the api use:

- ``:mod:`~kivy.module``` to refer to a module
- ``:class:`~kivy.module.Class``` to refer to a class
- ``:meth:`~kivy.module.Class.method``` to refer to a method
- ``:doc:`api-kivy.module``` to refer to the documentation of a module (same
  for a class and a method)

Obviously replacing `module` `class` and `method` with their real name, and
using using '.' to separate modules refering to imbricated modules, e.g::

    :mod:`~kivy.uix.floatlayout`
    :class:`~kivy.uix.floatlayout.FloatLayout`
    :meth:`~kivy.core.window.WindowBase.toggle_fullscreen`
    :doc:`/api-kivy.core.window`

Will result in:

    :mod:`~kivy.uix.floatlayout`
    :class:`~kivy.uix.floatlayout.FloatLayout`
    :meth:`~kivy.core.window.WindowBase.toggle_fullscreen`
    :doc:`/api-kivy.core.window`

`:doc:` and `:mod:` are essentially the same, except for an anchor in the url,
this makes `:doc:` prefered, for the cleaner url.

To build your documentation, run::

    make html

If you updated your kivy install, and have some trouble compiling docs, run::

    make clean force html

The doc will be generated in ``build/html``.

Unit tests contributions
------------------------

For testing team, we have the document :doc:`contribute-unittest` that
explain how Kivy unit test is working, and how you can create your own. Use the
same approach as the `Code Workflow` to submit new tests.

.. toctree::
    :maxdepth: 2

    contribute-unittest


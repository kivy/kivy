.. _contributing:

Contribution Guidelines
=======================

Kivy is a large product used by many thousands of developers for free,
but it is built entirely by the contributions of volunteers. We welcome (and rely on)
users who want to give back to the community by contributing to the project.

Contributions can come in many forms (See :ref:`Ways you can help out`.).
This chapter discusses how you can help us.

This chapter applies to the entire Kivy eco-system: the Kivy framework and all of
the sibling projects. However, check the documentation of individual projects in
case they have special instructions.

.. _Ways you can help out:

Ways you can help out
---------------------

* The most direct way is submitting source code changes: bug-fixes, new code and
  documentation amendments to improve the products. See :ref:`Code Contributions`
  and :ref:`Documentation Contributions` below for detailed instructions.

* Submitting bug reports and new feature suggestions in our Issue trackers is also
  welcome.

  If you are asking "Why did I get this error?" or "How do I implement this?"
  please **don't** raise an issue yet. Take it to our support channels instead (see :doc:`contact`); until we
  can be fairly confident it is a bug in the Kivy eco-system, it isn't ready to be raised
  as an issue. That said, we *do* want to hear about even the most minor typos or problems
  you find.

  See :ref:`reporting_issues` below for detailed instructions.

* You could help out by looking at the issues that other people have raised.

  * Tell us whether you can reproduce the error (on similar and/or different platforms). If the problem has already
    been fixed and no-one noticed, let us know!

  * If the submitter was unclear, shed whatever light you can. Submitting a short piece of code that
    demonstrates the problem is incredibly helpful. Providing details logs can give others the clues that
    they need.

  * Got some coding skills?

    * If you are new to Kivy, consider looking at the `Easy` or `Good First Issue` tags on each
      project while you learn the process.

    * Try some debugging? Even if you can't propose a solution, pointing out where
      the current code (or documentation) is wrong can be the difference between an issue
      floundering and getting quickly solved.

    * If you are a little more experienced, then take a look for issues where someone has
      proposed a detailed solution without submitting a PR. That's a great opportunity for
      a quick win.

    * Want to be a real hero? Become a foster parent for an old open PR, where the submitter
      has bitten off more than they can chew. It will need you to understand the problem they
      were solving, and understand how they were trying to solve it. You'll need to review it,
      and fix problems yourself. You will need to rebase it, so it can be merged. Then submit it again,
      and advocate for it until it is merged.

  * You know what is even rarer than coding skills on an open source project? Writing skills!
    If you can write clearly, there are plenty of documentation improvements that have been identified.

    * Can you identify a common question from support? Add the answer to the FAQ and save people time.

* You don't need to find a bug or come up with a new idea to contribute to the code base.

  * Review some code. See if you can spot flaws before they become bugs.

  * Refactor some code. Make it easier for the next person to understand and modify.

  * Add some unit-tests. It can be difficult to persuade occasional contributors to
    include sufficient unit tests. A solid bank of unit-tests makes further development
    much faster - your small effort can have long term benefits. See :doc:`contribute-unittest` for
    more about how our unit-tests are structured.

* Kivy is extensible. You can add a new Widget or a new Python-For-Android recipe, and have your
  code re-used by the community.

* Outside of the code and documentation, there are still so many ways to help.

  * Monitor the Discussions and Support Channels, and help beginners out.

  * Evangelise: Tell people about Kivy and what you are using it for. Give a talk about Kivy.

  * Submit your project to the Kivy gallery to show people what it can do.

    * Even if you don't want it showcased, tell us what you've done! It is very motivational to see others
      using your code successfully.

  * Persuade your organization to become a `sponsor <https://opencollective.com/kivy>`_.

There is no shortage of ways you can help The Open Source community is built on volunteers contributing what they can
when they can. Even if you aren't an experienced coder, you can make those that are more productive.


Planning
--------
If you want to discuss your contributions before you make them,
to get feedback and advice, you can ask us on the `#dev` channel of our `Discord <https://chat.kivy.org>`_ server.

The issue trackers are a more formal tracking mechanism, and
offer lots of opportunities to help out in ways that aren't just
submitting new code.

Code of Conduct
---------------

In the interest of fostering an open and welcoming community, we as
contributors and maintainers need to ensure participation in our project and our
sister projects is a harassment-free and positive experience for everyone. It is
vital that all interaction is conducted in a manner conveying respect, open-mindedness and gratitude.

We have adopted V2.1 of the `Contributor Covenant Code of Conduct
<https://www.contributor-covenant.org/version/2/1/code-of-conduct.html>`_.  Instances of abusive, harassing, or
otherwise unacceptable behavior may be reported to any of our `core developers <https://kivy.org/about.html>`_
via `Discord <https://chat.kivy.org>`_. (You might like to check which have been recently active on Discord to get a faster
response.)


.. _reporting_issues:

Reporting an Issue
------------------

If you found anything wrong - a bug in Kivy, missing documentation, incorrect
spelling or just unclear examples -  please take two minutes to report the issue.
(If you are unsure, please try our support channels first; see :doc:`contact` for details.)

If you can produce a small example of a program that fails, it helps immensely:

#. Move your logging level to debug by editing `<user_directory>/.kivy/config.ini`::

    [kivy]
    log_level = debug

#. Execute your code again, and copy/paste the complete output to http://gist.github.com/,
   including the log from Kivy and the python backtrace.

To raise the issue:

#. Open the Github issue database appropriate for the project - e.g. `Kivy Framework <https://github.com/kivy/kivy/issues/>`_, `Buildozer <https://github.com/kivy/buildozer/issues/>`_, `python-for-android <https://github.com/kivy/python-for-android/issues/>`_, `kivy-ios <https://github.com/kivy/kivy-ios/issues/>`_, etc.
#. Set the title of your issue
#. Explain exactly what to do to reproduce the issue and paste the link of the output
   posted on http://gist.github.com/
#. Validate the issue and you're done!

.. _Code Contributions:

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

- If you haven't done it yet, read the
  `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ about coding style in python.

- If you  are working on the Kivy Framework, you can automate style checks on
  Github commit:

  If are developing on Unix or OSX or otherwise have ``make`` installed, change to the Kivy source directory, and
  simply run::

    make hook


  This will pass the code added to the git staging zone (about to be committed)
  through a checker program when you do a commit, and ensure that you didn't
  introduce style errors. If you did, the commit will be rejected: please correct the
  errors and try again.

  The checker used is `pre-commit <https://pre-commit.com/>`_. If you need to skip
  a particular check see `documentation <https://pre-commit.com/#temporarily-disabling-hooks>`_,
  but, in summmary, putting `SKIP=hookname` in front of `git commit` will skip that hook. The
  name of the offending hook is shown when it fails.

Performance
~~~~~~~~~~~

- Take care of performance issues: read
  `Python performance tips <http://wiki.python.org/moin/PythonSpeed/PerformanceTips>`_
- CPU-intensive parts of Kivy are written in Cython: if you are doing a lot of
  computation, consider using it too.

Git & GitHub
~~~~~~~~~~~~

We use git as our version control system for our code base. If you have never
used git or a similar DVCS (or even any VCS) before, we strongly suggest you
take a look at the great documentation that is available for git online.
The `Git Community Book <http://book.git-scm.com/>`_ or the
`Git Videos <https://git-scm.com/videos>`_ are both great ways to learn git.
Trust us when we say that git is a great tool. It may seem daunting at first,
but after a while you'll (hopefully) love it as much as we do. Teaching you git,
however, is well beyond the scope of this document.

Also, we use `GitHub <http://github.com>`_ to host our code. In the following we
will assume that you have a (free) GitHub account. While this part is optional,
it allows for a tight integration between your patches and our upstream code
base. If you don't want to use GitHub, we assume you know what you are doing anyway.

Code Workflow
~~~~~~~~~~~~~

These instructions are written from the perspective of the Kivy framework, but their
equivalents apply to other Kivy sibling projects.

The initial setup to begin with our workflow only needs to be done once.
Follow the installation instructions from :ref:`kivy-dev-install`, but don't clone our repository.
Instead, make a fork. Here are the steps:

#. Log in to GitHub
#. Create a fork of the `Kivy repository <https://github.com/kivy/kivy>`_ by
   clicking the *fork* button.
#. Clone your fork of our repository to your computer. Your fork will have
   the git remote name 'origin' and you will be on branch 'master'::

        git clone https://github.com/username/kivy.git

#. Compile and set up PYTHONPATH or install (see :ref:`kivy-dev-install`_).
#. Add the kivy repo as a remote source::

        git remote add kivy https://github.com/kivy/kivy.git

    Now, whenever you want to create a patch, you follow the following steps:

#.  See if there is a ticket in our bug tracker for the fix or feature and
    announce that you'll be working on it if it doesn't yet have an assignee.
#.  Create a new, appropriately named branch in your local repository for
    that specific feature or bugfix.
    (Keeping a new branch per feature makes sure we can easily pull in your
    changes without pulling any other stuff that is not supposed to be pulled.)::

        git checkout -b new_feature

#. Modify the code to do what you want (e.g. fix it).
#. Test the code. Add automated unit-tests to show it works. Do this even for small fixes.
   You never know whether you have introduced some weird bug without testing.
#. Do one or more minimal, atomic commits per fix or per feature.
   Minimal/Atomic means *keep the commit clean*. Don't commit other stuff that
   doesn't logically belong to this fix or feature. This is **not** about
   creating one commit per line changed. Use ``git add -p`` if necessary.
#. Give each commit an appropriate commit message, so that others who are
   not familiar with the matter get a good idea of what you changed.
#. Once you are satisfied with your changes, pull our upstream repository and
   merge it with you local repository. We can pull your stuff, but since you know
   exactly what's changed, you should do the merge::

        git pull kivy master

#. Push your local branch into your remote repository on GitHub::

        git push origin new_feature

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


.. _Documentation Contributions:

Documentation Contributions
---------------------------

Documentation contributions generally follow the same workflow as code contributions,
but are just a bit more lax.

#. Follow the instructions above

   #. Fork the repository.
   #. Clone your fork to your computer.
   #. Setup kivy repo as a remote source.

#. Install python-sphinx. (See ``docs/README`` for assistance.)

#. Use ReStructuredText_Markup_ to make changes to the HTML documentation in docs/sources.

.. _ReStructuredText_Markup: http://docutils.sourceforge.net/rst.html

To submit a documentation update, use the following steps:

#. Create a new, appropriately named branch in your local repository::

        git checkout -b my_docs_update

#. Modify the documentation with your correction or improvement.
#. Re-generate the HTML pages, and review your update::

            make html

#. Give each commit an appropriate commit message, so that others who are not familiar with
   the matter get a good idea of what you changed.
#. Keep each commit focused on a single related theme. Don't commit other stuff that doesn't
   logically belong to this update.

#. Push to your remote repository on GitHub::

        git push

#. Send a *Pull Request* with a description of what you changed via the button in the
       GitHub interface of your repository.

We don't ask you to go through all the hassle just to correct a single typo, but for more
complex contributions, please follow the suggested workflow.

Docstrings
~~~~~~~~~~

Every module/class/method/function needs a docstring, so use the following keywords
when relevant:

- ``.. versionadded::`` to mark the version in which the feature was added.
- ``.. versionchanged::`` to mark the version in which the behaviour of the feature was
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

Will result in::

    def my_new_feature(self, arg):
        New feature is awesome

        .. versionadded:: 1.1.4

        .. note:: This new feature will likely blow your mind

        .. warning:: Please take a seat before trying this feature



When referring to other parts of the api use:

- ``:mod:`~kivy.module``` to refer to a module
- ``:class:`~kivy.module.Class``` to refer to a class
- ``:meth:`~kivy.module.Class.method``` to refer to a method
- ``:doc:`api-kivy.module``` to refer to the documentation of a module (same
  for a class and a method)

Obviously replacing `module` `Class` and `method` with their real name, and
using using '.' to separate modules referring to imbricated modules, e.g::

    :mod:`~kivy.uix.floatlayout`
    :class:`~kivy.uix.floatlayout.FloatLayout`
    :meth:`~kivy.core.window.WindowBase.toggle_fullscreen`
    :doc:`/api-kivy.core.window`

Will result in::

 :mod:`~kivy.uix.floatlayout`
 :class:`~kivy.uix.floatlayout.FloatLayout`
 :meth:`~kivy.core.window.WindowBase.toggle_fullscreen`
 :doc:`/api-kivy.core.window`

The markers `:doc:` and `:mod:` are essentially the same, except for an anchor in the url
which makes `:doc:` preferred for the cleaner url.

To build your documentation, run::

    make html

If you updated your kivy install, and have some trouble compiling docs, run::

    make clean force html

The docs will be generated in ``docs/build/html``. For more information on
docstring formatting, please refer to the official
`Sphinx Documentation <http://sphinx-doc.org/>`_.

Unit tests contributions
------------------------

For the testing team, we have the document :doc:`contribute-unittest` that
explains how Kivy unit tests work and how you can create your own. Use the
same approach as the `Code Workflow` to submit new tests.

.. toctree::
    :maxdepth: 2

    contribute-unittest

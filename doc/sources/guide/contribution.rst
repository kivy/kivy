Contribution
============

Coding rules
------------

- If you didn't do it yet, read the PEP8 about coding style in python
  http://www.python.org/dev/peps/pep-0008/.
- Activate pep8 check on git commit like this::

    make hook

This will pass the code added to git staging zone (about to be committed)
thought a pep8 checker program when you do a commit, and check that you didn't
introduce pep8 errors, if so, the commit will be rejected, correct the errors,
and try again.

Documentation
-------------

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

Will result in 

    :mod:`~kivy.uix.floatlayout`
    :class:`~kivy.uix.floatlayout.FloatLayout`
    :meth:`~kivy.core.window.WindowBase.toggle_fullscreen`
    :doc:`/api-kivy.core.window`

`:doc:` and `:mod:` are essentially the same, except for an anchor in the url,
this makes `:doc:` prefered, for the cleaner url.

Tests
-----

Tests in kivy are easy to write, they are based on the unittest module and easy
to start, think about them, tests makes a project stronger !

Look into `kivy/tests` and, if you encounter a bug in kivy, or add a feature to
kivy, please try to write a simple tests that tries the concerned feature,
showing a potential bug.


Performances
------------

- take care of performance issues, read
  http://wiki.python.org/moin/PythonSpeed/PerformanceTips
- cpu intensive parts of Kivy are written in cython, if you are doing a lot of
  computation, consider using it too.

Workflow
--------

- For new features or big corrections, consider creating a branch on your fork,
  and do the pull request from the branch.

Example using git command line, assuming you forked kivy on github and cloned
locally using the url provided by github:

Creating a branch::

    git chekcout -b my_new_feature

Do some changes, add them to the future commit::

    git add -p

If you created files that need to be tracked::

    git add filenames

Then commit::

    git commit

If your commit fixes a bug referenced in the tracker, putting::

    closes: #XXX

in the commit message is a good thing, XXX being the issue number.

Please think about committing regularly, committing when things works better
than the last commits, is a good rule

Push your changes to your github repos::

    git push

Then, from the Github repos, click on the `pull request` button at the top of
the page, make sure you are requesting your merge to be done from your feature
branch to kivy master branch, and add a short text describing why you think
your changes should be merged.

You can do a pull request even if you are not totally sure you followed all the
recomendations to the letter, we will review and suggest changes if we feel
some more work is required, the pull request will be automatically updated when
you'll push new changes, so no worry doing the pull request early.

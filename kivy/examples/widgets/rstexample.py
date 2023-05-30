'''
QuickReference for Rst
======================

This is a markup example: [b]Hello[/b] [i]world[/i]
And if i really want to write my code: &amp;bl; Hello world &amp;br;

And video widget
----------------

.. video:: cityCC0.mpg


Inline Markup
-------------

- *emphasis*
- **strong emphasis**
- `interpreted text`
- ``inline literal``
- reference_
- `phrase reference`_
- anonymous__
- _`inline internal target`

.. _top:

Internal cross-references, like example_, or bottom_.

Image
-----

Woot!

What about a little image ?

.. image:: kivy/data/logo/kivy-icon-256.png

Grid
----

+------------+------------+-----------+
| Header 1   | Header 2   | Header 3  |
+============+============+===========+
| body row 1 | column 2   | column 3  |
+------------+------------+-----------+
| body row 2 | column 2   | column 3  |
+------------+------------+-----------+
| body row 3 | column 2   | column 3  |
+------------+------------+-----------+

Term list
---------

:Authors:
    Tony J. (Tibs) Ibbs,
    David Goodger
    (and sundry other good-natured folks)

.. _example:

:Version: 1.0 of 2001/08/08
:Dedication: To my father.

Definition list
---------------

what
  Definition lists associate a term with a definition.

how
  The term is a one-line phrase, and the definition is one or more paragraphs
  or body elements, indented relative to the term. Blank lines are not allowed
  between term and definition.


Block quotes
------------

Block quotes are just:

    Indented paragraphs,

        and they may nest.

Admonitions
-----------

.. warning::

    This is just a Test.

.. note::

    And this is just a note. Let's test some literal::

        $ echo 'Hello world'
        Hello world

Ordered list
------------

#. My item number one
#. My item number two with some more content
   and it's continuing on the second line?
#. My third item::

    Oh wait, we can put code!

#. My four item::

    No way.

.. _bottom:

Go to top_'''

from kivy.uix.rst import RstDocument
from kivy.app import App


class RstApp(App):
    def build(self):
        return RstDocument(text=__doc__)


if __name__ == '__main__':
    RstApp().run()

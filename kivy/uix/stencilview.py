'''
Stencil View
============

.. versionadded:: 1.0.4

A :class:`StencilView` is a class that limit the drawing of his children widgets
to his bounding box. Any drawing outside the bounding box of the widget will be
trashed.

The StencilView use the stencil graphics instructions to make it work. It
provides an efficient way to clip the drawing area of its children.

.. note::

    As the stencil graphics instructions, you cannot stack more than 8
    stencil-aware widgets.

'''

__all__ = ('StencilView', )

from kivy.uix.widget import Widget


class StencilView(Widget):
    '''StencilView class. See module documentation for more information.
    '''
    pass


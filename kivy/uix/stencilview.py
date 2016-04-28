'''
Stencil View
============

.. image:: images/stencilview.gif
    :align: right

.. versionadded:: 1.0.4

:class:`StencilView` limits the drawing of child widgets to the StencilView's
bounding box. Any drawing outside the bounding box will be clipped (trashed).

The StencilView uses the stencil graphics instructions under the hood. It
provides an efficient way to clip the drawing area of children.

.. note::

    As with the stencil graphics instructions, you cannot stack more than 128
    stencil-aware widgets.

.. note::

    StencilView is not a layout. Consequently, you have to manage the size and
    position of its children directly. You can combine (subclass both)
    a StencilView and a Layout in order to achieve a layout's behavior.
    For example::

        class BoxStencil(BoxLayout, StencilView):
            pass
'''

__all__ = ('StencilView', )

from kivy.uix.widget import Widget


class StencilView(Widget):
    '''StencilView class. See module documentation for more information.
    '''
    pass

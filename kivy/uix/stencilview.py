'''
Stencil View
============

.. versionadded:: 1.0.4

:class:`StencilView` limits the drawing of child widgets to the StencilView's
bounding box. Any drawing outside the bounding box will be clipped (trashed).

The StencilView uses the stencil graphics instructions under the hood. It
provides an efficient way to clip the drawing area of children.

.. note::

    As with the stencil graphics instructions, you cannot stack more than 8
    stencil-aware widgets.

.. note::

    StencilView is not a layout, consequently, you have to manage the size and
    position of the children directly. You can combine a StencilView with a
    layout in order to have both a layout and stencilview behavior. For
    example::

        class BoxStencil(BoxLayout, StencilView):
            pass
'''

__all__ = ('StencilView', )

from kivy.uix.widget import Widget


class StencilView(Widget):
    '''StencilView class. See module documentation for more information.
    '''
    pass

"""
Tesselator
==========

.. versionadded:: 1.9.0

.. image:: images/tesselator-filled.png
    :align: right
.. image:: images/tesselator-debug.png
    :align: right

.. warning::

    This is experimental and subject to change as long as this warning notice
    is present. Only TYPE_POLYGONS is currently supported.

Tesselator is a library for tesselating polygons, based on
`libtess2 <https://github.com/memononen/libtess2>`_. It renders concave filled
polygons by first tesselating them into convex polygons. It also supports holes.

Usage
-----

First, you need to create a :class:`Tesselator` object and add contours. The
first one is the external contour of your shape and all of the following ones
should be holes::

    from kivy.graphics.tesselator import Tesselator

    tess = Tesselator()
    tess.add_contour([0, 0, 200, 0, 200, 200, 0, 200])
    tess.add_contour([50, 50, 150, 50, 150, 150, 50, 150])

Second, call the :meth:`Tesselator.tesselate` method to compute the points. It
is possible that the tesselator won't work. In that case, it can return
False::

    if not tess.tesselate():
        print "Tesselator didn't work :("
        return

After the tessellation, you have multiple ways to iterate over the result. The
best approach is using :data:`Tesselator.meshes` to get a format directly usable
for a :class:`~kivy.graphics.Mesh`::

    for vertices, indices in tess.meshes:
        self.canvas.add(Mesh(
            vertices=vertices,
            indices=indices,
            mode="triangle_fan"
        ))

Or, you can get the "raw" result, with just polygons and x/y coordinates with
:meth:`Tesselator.vertices`::

    for vertices in tess.vertices:
        print "got polygon", vertices

"""

__all__ = ("Tesselator", "WINDING_ODD", "WINDING_NONZERO", "WINDING_POSITIVE",
           "WINDING_NEGATIVE", "TYPE_POLYGONS", "TYPE_BOUNDARY_CONTOURS")

include "common.pxi"
cimport cython
cimport cpython.array
from array import array
from cython cimport view

cdef extern from "tesselator.h":
    ctypedef struct TESStesselator:
        pass
    ctypedef struct TESSalloc:
        pass
    cdef enum TessElementType:
        TESS_POLYGONS
        TESS_CONNECTED_POLYGONS
        TESS_BOUNDARY_CONTOURS
    cdef enum TessWindingRule:
        TESS_WINDING_ODD
        TESS_WINDING_NONZERO
        TESS_WINDING_POSITIVE
        TESS_WINDING_NEGATIVE
        TESS_WINDING_ABS_GEQ_TWO
    TESStesselator *tessNewTess(TESSalloc *)
    void tessDeleteTess(TESStesselator *)
    void tessAddContour(TESStesselator *, int, void *, int, int)
    int tessTesselate(TESStesselator *, int, int, int, int, float *)
    int tessGetVertexCount(TESStesselator *)
    int tessGetElementCount(TESStesselator *)
    float *tessGetVertices(TESStesselator *)
    int *tessGetVertexIndices(TESStesselator *)
    int *tessGetElements(TESStesselator *)


#: Winding enum: ODD
WINDING_ODD = TESS_WINDING_ODD

#: Winding enum: NONZERO
WINDING_NONZERO = TESS_WINDING_NONZERO

#: Winding enum: POSITIVE
WINDING_POSITIVE = TESS_WINDING_POSITIVE

#: Winding enum: NEGATIVE
WINDING_NEGATIVE = TESS_WINDING_NEGATIVE

#: Winding enum: ABS_GET_TWO
WINDING_ABS_GEQ_TWO = TESS_WINDING_ABS_GEQ_TWO

#: Element type enum: POLYGONS
TYPE_POLYGONS = TESS_POLYGONS

#: Element type enum: BOUNDARY_CONTOURS
TYPE_BOUNDARY_CONTOURS = TESS_BOUNDARY_CONTOURS


cdef int TESS_UNDEF = ~(<int>0)


cdef class Tesselator:
    """Tesselator class. See module for more informations about the usage.
    """
    def __cinit__(self):
        self.tess = tessNewTess(NULL)

    def __dealloc__(self):
        tessDeleteTess(<TESStesselator *>self.tess)
        self.tess = NULL

    def add_contour(self, points):
        """
        Add a contour to the tesselator. It can be:

        - a list of `[x, y, x2, y2, ...]` coordinates
        - a float array: `array("f", [x, y, x2, y2, ...])`
        - any buffer with floats in it.
        """
        cdef float [:] float_view
        cdef char *cdata
        cdef long datasize
        cdef long count

        if isinstance(points, (tuple, list)):
            float_view = array("f", points)
        else:
            # must be a memory view or a buffer type
            float_view = points

        cdata = <char *>&float_view[0]
        datasize = float_view.nbytes
        self.add_contour_data(cdata, len(points) / 2)

    cpdef int tesselate(
            self, int winding_rule=WINDING_ODD,
            int element_type=TYPE_POLYGONS, int polysize=65535):
        """
        Compute all the contours added with :meth:`add_contour`, and generate
        polygons.

        :Parameters:
            `winding_rule`: enum
                The winding rule classifies a region as inside if its winding
                number belongs to the chosen category. Can be one of
                WINDING_ODD, WINDING_NONZERO, WINDING_POSITIVE,
                WINDING_NEGATIVE, WINDING_ABS_GEQ_TWO. Defaults to WINDING_ODD.
            `element_type`: enum
                The result type, you can generate the polygons with
                TYPE_POLYGONS, or the contours with TYPE_BOUNDARY_CONTOURS.
                Defaults to TYPE_POLYGONS.
        :return: 1 if the tessellation happened, 0 otherwise.
        :rtype: int

        """

        self.element_type = element_type
        self.polysize = polysize
        return tessTesselate(<TESStesselator *>self.tess, winding_rule, element_type,
                            polysize, 2, NULL)

    @property
    def vertex_count(self):
        """Returns the number of vertex generated.

        This is the raw result, however, because the Tesselator format the
        result for you with :data:`meshes` or :data:`vertices` per polygon,
        you'll have more vertices in the result
        """
        return tessGetVertexCount(<TESStesselator *>self.tess)

    @property
    def element_count(self):
        """Returns the number of convex polygon.
        """
        return tessGetElementCount(<TESStesselator *>self.tess)

    @property
    def vertices(self):
        """
        Iterate through the result of the :meth:`tesselate` in order to give
        only a list of `[x, y, x2, y2, ...]` polygons.
        """
        return self.iterate_vertices(0)

    @property
    def meshes(self):
        """
        Iterate through the result of the :meth:`tesselate` to give a result
        that can be easily pushed into Kivy`s Mesh object.

        It's a list of: `[[vertices, indices], [vertices, indices], ...]`.
        The vertices in the format `[x, y, u, v, x2, y2, u2, v2]`.

        Careful, u/v coordinates are the same as x/y.
        You are responsible to change them for texture mapping if you need to.

        You can create Mesh objects like that::

            tess = Tesselator()
            # add contours here
            tess.tesselate()
            for vertices, indices in self.meshes:
                self.canvas.add(Mesh(
                    vertices=vertices,
                    indices=indices,
                    mode="triangle_fan"))
        """
        return self.iterate_vertices(1)

    cdef void add_contour_data(self, void *cdata, int count):
        tessAddContour(<TESStesselator *>self.tess, 2, <void *>cdata, sizeof(float) * 2, count)

    @cython.boundscheck(False)
    cdef iterate_vertices(self, int mode):
        # mode 0: returns for .vertices
        # mode 1: returns for .meshes

        cdef int nelems, i, j, count
        cdef int *poly
        cdef int *elems
        cdef float *verts = <float *>tessGetVertices(<TESStesselator *>self.tess)
        cdef view.array mesh
        cdef float[:] f_mesh
        ret = []
        if self.element_type == TYPE_POLYGONS:
            nelems = tessGetElementCount(<TESStesselator *>self.tess)
            elems = <int *>tessGetElements(<TESStesselator *>self.tess)
            for i in range(nelems):
                poly = &elems[i * self.polysize]

                # first, count the number of vertices in this polygon
                count = 0
                for j in range(self.polysize):
                    if poly[j] == TESS_UNDEF:
                        break
                    count += 1

                # second, wrote it
                if not count:
                    continue

                if mode == 0:
                    # only x/y per polygon
                    mesh = view.array(shape=(count * 2, ),
                                      itemsize=sizeof(float), format="f")
                    f_mesh = mesh
                    for j in range(count):
                        f_mesh[j * 2] = verts[poly[j] * 2]
                        f_mesh[j * 2 + 1] = verts[poly[j] * 2 + 1]
                    ret.append(mesh.memview)

                elif mode == 1:
                    # mode that can fit to actual Kivy Mesh
                    # x, y, u, v
                    mesh = view.array(shape=(count * 4, ),
                                      itemsize=sizeof(float), format="f")
                    f_mesh = mesh
                    for j in range(count):
                        f_mesh[j * 4] = f_mesh[j * 4 + 2] = verts[poly[j] * 2]
                        f_mesh[j * 4 + 1] = f_mesh[j * 4 + 3] = verts[poly[j] * 2 + 1]
                    ret.append((mesh.memview, range(count)))

                else:
                    raise Exception("Invalid mode")
        else:
            # TODO implement TYPE_BOUNDARY_CONTOURS
            raise NotImplementedError()

        return ret

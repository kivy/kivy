DEF LINE_CAP_NONE = 0
DEF LINE_CAP_SQUARE = 1
DEF LINE_CAP_ROUND = 2

DEF LINE_JOINT_NONE = 0
DEF LINE_JOINT_MITER = 1
DEF LINE_JOINT_BEVEL = 2
DEF LINE_JOINT_ROUND = 3

cdef inline int line_intersection(double x1, double y1, double x2, double y2,
        double x3, double y3, double x4, double y4, double *px, double *py):
    cdef double u = (x1 * y2 - y1 * x2)
    cdef double v = (x3 * y4 - y3 * x4)
    cdef double denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return 0
    px[0] = (u * (x3 - x4) - (x1 - x2) * v) / denom
    py[0] = (u * (y3 - y4) - (y1 - y2) * v) / denom
    return 1

cdef class Line(VertexInstruction):
    '''A 2d line.

    .. versionadded:: 1.0.8
        `dash_offset` and `dash_length` have been added

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
        `dash_length`: int
            Length of a segment (if dashed), default 1
        `dash_offset`: int
            Offset between the end of a segments and the begining of the
            next one, default 0, changing this makes it dashed.
        `width`: float
            Width of the line, default 1.0
    '''
    cdef int _cap
    cdef int _cap_precision
    cdef int _joint
    cdef list _points
    cdef float _width
    cdef int _dash_offset, _dash_length

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('points')
        self.points = v if v is not None else []
        self.batch.set_mode('line_strip')
        self._dash_length = kwargs.get('dash_length') or 1
        self._dash_offset = kwargs.get('dash_offset') or 0
        self._width = kwargs.get('width') or 1.0
        self.joint = kwargs.get('joint') or 'round'
        self.cap = kwargs.get('cap') or 'round'
        self._cap_precision = kwargs.get('cap_precision') or 10

    cdef void build(self):
        if self._width == 1.0:
            self.build_legacy()
        else:
            self.build_extended()

    cdef void build_legacy(self):
        cdef int i, count = len(self.points) / 2
        cdef list p = self.points
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef float tex_x
        cdef char *buf = NULL
        cdef Texture texture = self.texture

        if count < 2:
            self.batch.clear_data()
            return

        self.batch.set_mode('line_strip')
        if self._dash_offset != 0:
            if texture is None or texture._width != \
                (self._dash_length + self._dash_offset) or \
                texture._height != 1:

                self.texture = texture = Texture.create(
                        size=(self._dash_length + self._dash_offset, 1))
                texture.wrap = 'repeat'

            # create a buffer to fill our texture
            buf = <char *>malloc(4 * (self._dash_length + self._dash_offset))
            memset(buf, 255, self._dash_length * 4)
            memset(buf + self._dash_length * 4, 0, self._dash_offset * 4)
            p_str = PyString_FromStringAndSize(buf,  (self._dash_length + self._dash_offset) * 4)

            self.texture.blit_buffer(p_str, colorfmt='rgba', bufferfmt='ubyte')
            free(buf)

        elif texture is not None:
            self.texture = None

        vertices = <vertex_t *>malloc(count * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc(count * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        tex_x = 0
        for i in xrange(count):
            if self._dash_offset != 0 and i > 0:
                tex_x += sqrt(
                        pow(p[i * 2]     - p[(i - 1) * 2], 2)  +
                        pow(p[i * 2 + 1] - p[(i - 1) * 2 + 1], 2)) / (
                                self._dash_length + self._dash_offset)

                vertices[i].s0 = tex_x
                vertices[i].t0 = 0

            vertices[i].x = p[i * 2]
            vertices[i].y = p[i * 2 + 1]
            indices[i] = i

        self.batch.set_data(vertices, count, indices, count)

        free(vertices)
        free(indices)

    cdef void build_extended(self):
        # TODO: current implementation doesn't support alpha well.
        cdef int i, j, count = len(self.points) / 2
        cdef list p = self.points
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef float tex_x
        cdef char *buf = NULL
        cdef Texture texture = self.texture

        if count < 2:
            self.batch.clear_data()
            return

        self.batch.set_mode('triangles')
        cdef unsigned int vertices_count = (count - 1) * 4
        cdef unsigned int indices_count = (count - 1) * 6
        cdef unsigned int iv = 0, ii = 0

        if self._joint == LINE_JOINT_BEVEL:
            indices_count += (count - 2) * 3
            vertices_count += (count - 2)
        elif self._joint == LINE_JOINT_ROUND:
            indices_count += (self._cap_precision * 3) * (count - 2)
            vertices_count += (self._cap_precision + 1) * (count - 2)
        elif self._joint == LINE_JOINT_MITER:
            indices_count += (count - 2) * 6
            vertices_count += (count - 2) * 2

        if self._cap == LINE_CAP_SQUARE:
            indices_count += 12
            vertices_count += 4
        elif self._cap == LINE_CAP_ROUND:
            indices_count += (self._cap_precision * 3) * 2
            vertices_count += (self._cap_precision + 1) * 2

        vertices = <vertex_t *>malloc(vertices_count * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc(indices_count * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        cdef double ax, ay, bx, by, cx, cy, angle, a1, a2
        cdef double x1, y1, x2, y2, x3, y3, x4, y4
        cdef double sx1, sy1, sx4, sy4, sangle
        cdef double pcx, pcy, px1, py1, px2, py2, px3, py3, px4, py4, pangle, pangle2
        cdef double w = self._width
        cdef double ix, iy
        cdef unsigned int pii, piv, pii2, piv2
        cdef double jangle
        pii = piv = pcx = pcy = cx = cy = ii = iv = ix = iy = 0
        for i in range(0, count - 1):
            ax = p[i * 2]
            ay = p[i * 2 + 1]
            bx = p[i * 2 + 2]
            by = p[i * 2 + 3]

            if i > 0 and self._joint != LINE_JOINT_NONE:
                pcx = cx
                pcy = cy
                px1 = x1
                px2 = x2
                px3 = x3
                px4 = x4
                py1 = y1
                py2 = y2
                py3 = y3
                py4 = y4

            pii2 = pii
            piv2 = piv
            pii = ii
            piv = iv
            pangle2 = pangle
            pangle = angle

            # calculate the orientation of the segment, between pi and -pi
            cx = bx - ax
            cy = by - ay
            angle = atan2(cy, cx)
            a1 = angle - PI2
            a2 = angle + PI2

            # calculate the position of the segment
            x1 = ax + cos(a1) * w
            y1 = ay + sin(a1) * w
            x4 = ax + cos(a2) * w
            y4 = ay + sin(a2) * w
            x2 = bx + cos(a1) * w
            y2 = by + sin(a1) * w
            x3 = bx + cos(a2) * w
            y3 = by + sin(a2) * w

            if i == 0:
                sx1 = x1
                sy1 = y1
                sx4 = x4
                sy4 = y4
                sangle = angle

            indices[ii    ] = iv
            indices[ii + 1] = iv + 1
            indices[ii + 2] = iv + 2
            indices[ii + 3] = iv
            indices[ii + 4] = iv + 2
            indices[ii + 5] = iv + 3
            ii += 6

            vertices[iv].x = x1
            vertices[iv].y = y1
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = x2
            vertices[iv].y = y2
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = x3
            vertices[iv].y = y3
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = x4
            vertices[iv].y = y4
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1

            # joint generation
            if i == 0 or self._joint == LINE_JOINT_NONE:
                continue

            # calculate the angle of the previous and current segment
            jangle = atan2(
                cx * pcy - cy * pcx,
                cx * pcx + cy * pcy)

            # in case of the angle is NULL, avoid the generation
            if jangle == 0 or jangle == PI or jangle == -PI:
                if self._joint == LINE_JOINT_BEVEL:
                    vertices_count -= 1
                    indices_count -= 3
                elif self._joint == LINE_JOINT_MITER:
                    vertices_count -= 2
                    indices_count -= 6
                continue

            if self._joint == LINE_JOINT_BEVEL:
                vertices[iv].x = ax
                vertices[iv].y = ay
                vertices[iv].s0 = 0
                vertices[iv].t0 = 0
                if jangle < 0:
                    indices[ii] = piv2 + 1
                    indices[ii + 1] = piv
                    indices[ii + 2] = iv
                else:
                    indices[ii] = piv2 + 2
                    indices[ii + 1] = piv + 3
                    indices[ii + 2] = iv
                ii += 3
                iv += 1

            elif self._joint == LINE_JOINT_MITER:
                vertices[iv].x = ax
                vertices[iv].y = ay
                vertices[iv].s0 = 0
                vertices[iv].t0 = 0
                if jangle < 0:
                    if line_intersection(px1, py1, px2, py2, x1, y1, x2, y2, &ix, &iy) == 0:
                        vertices_count -= 2
                        indices_count -= 6
                        continue
                    vertices[iv + 1].x = ix
                    vertices[iv + 1].y = iy
                    vertices[iv + 1].s0 = 0
                    vertices[iv + 1].t0 = 0
                    indices[ii] = iv
                    indices[ii + 1] = iv + 1
                    indices[ii + 2] = piv2 + 1
                    indices[ii + 3] = iv
                    indices[ii + 4] = piv
                    indices[ii + 5] = iv + 1
                    ii += 6
                    iv += 2
                else:
                    if line_intersection(px3, py3, px4, py4, x3, y3, x4, y4, &ix, &iy) == 0:
                        vertices_count -= 2
                        indices_count -= 6
                        continue
                    vertices[iv + 1].x = ix
                    vertices[iv + 1].y = iy
                    vertices[iv + 1].s0 = 0
                    vertices[iv + 1].t0 = 0
                    indices[ii] = iv
                    indices[ii + 1] = iv + 1
                    indices[ii + 2] = piv2 + 2
                    indices[ii + 3] = iv
                    indices[ii + 4] = piv + 3
                    indices[ii + 5] = iv + 1
                    ii += 6
                    iv += 2



            elif self._joint == LINE_JOINT_ROUND:

                # cap end
                if jangle < 0:
                    a1 = pangle2 - PI2
                    a2 = angle + PI2
                    a0 = a2
                    step = (abs(jangle)) / float(self._cap_precision)
                    pivstart = piv + 3
                    pivend = piv2 + 1
                else:
                    a1 = angle - PI2
                    a2 = pangle2 + PI2
                    a0 = a1
                    step = -(abs(jangle)) / float(self._cap_precision)
                    pivstart = piv
                    pivend = piv2 + 2
                siv = iv
                vertices[iv].x = ax
                vertices[iv].y = ay
                vertices[iv].s0 = 0
                vertices[iv].t0 = 0
                iv += 1
                for j in xrange(0, self._cap_precision - 1):
                    vertices[iv].x = ax - cos(a0 - step * j) * w
                    vertices[iv].y = ay - sin(a0 - step * j) * w
                    vertices[iv].s0 = 0
                    vertices[iv].t0 = 0
                    if j == 0:
                        indices[ii] = siv
                        indices[ii + 1] = pivstart
                        indices[ii + 2] = iv
                    else:
                        indices[ii] = siv
                        indices[ii + 1] = iv - 1
                        indices[ii + 2] = iv
                    iv += 1
                    ii += 3
                indices[ii] = siv
                indices[ii + 1] = iv - 1
                indices[ii + 2] = pivend
                ii += 3

        # caps
        if self._cap == LINE_CAP_SQUARE:
            vertices[iv].x = x2 + cos(angle) * w
            vertices[iv].y = y2 + sin(angle) * w
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            vertices[iv + 1].x = x3 + cos(angle) * w
            vertices[iv + 1].y = y3 + sin(angle) * w
            vertices[iv + 1].s0 = 0
            vertices[iv + 1].t0 = 0
            indices[ii] = piv + 1
            indices[ii + 1] = piv + 2
            indices[ii + 2] = iv + 1
            indices[ii + 3] = piv + 1
            indices[ii + 4] = iv
            indices[ii + 5] = iv + 1
            ii += 6
            iv += 2
            vertices[iv].x = sx1 - cos(sangle) * w
            vertices[iv].y = sy1 - sin(sangle) * w
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            vertices[iv + 1].x = sx4 - cos(sangle) * w
            vertices[iv + 1].y = sy4 - sin(sangle) * w
            vertices[iv + 1].s0 = 0
            vertices[iv + 1].t0 = 0
            indices[ii] = 0
            indices[ii + 1] = 3
            indices[ii + 2] = iv + 1
            indices[ii + 3] = 0
            indices[ii + 4] = iv
            indices[ii + 5] = iv + 1
            ii += 6
            iv += 2

        elif self._cap == LINE_CAP_ROUND:

            # cap start
            a1 = sangle - PI2
            a2 = sangle + PI2
            step = (a1 - a2) / float(self._cap_precision)
            siv = iv
            cx = p[0]
            cy = p[1]
            vertices[iv].x = cx
            vertices[iv].y = cy
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            for i in xrange(0, self._cap_precision - 1):
                vertices[iv].x = cx + cos(a1 + step * i) * w
                vertices[iv].y = cy + sin(a1 + step * i) * w
                vertices[iv].s0 = 0
                vertices[iv].t0 = 0
                if i == 0:
                    indices[ii] = siv
                    indices[ii + 1] = 0
                    indices[ii + 2] = iv
                else:
                    indices[ii] = siv
                    indices[ii + 1] = iv - 1
                    indices[ii + 2] = iv
                iv += 1
                ii += 3
            indices[ii] = siv
            indices[ii + 1] = iv - 1
            indices[ii + 2] = 3
            ii += 3

            # cap end
            a1 = angle - PI2
            a2 = angle + PI2
            step = (a2 - a1) / float(self._cap_precision)
            siv = iv
            cx = p[-2]
            cy = p[-1]
            vertices[iv].x = cx
            vertices[iv].y = cy
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            for i in xrange(0, self._cap_precision - 1):
                vertices[iv].x = cx + cos(a1 + step * i) * w
                vertices[iv].y = cy + sin(a1 + step * i) * w
                vertices[iv].s0 = 0
                vertices[iv].t0 = 0
                if i == 0:
                    indices[ii] = siv
                    indices[ii + 1] = piv + 1
                    indices[ii + 2] = iv
                else:
                    indices[ii] = siv
                    indices[ii + 1] = iv - 1
                    indices[ii + 2] = iv
                iv += 1
                ii += 3
            indices[ii] = siv
            indices[ii + 1] = iv - 1
            indices[ii + 2] = piv + 2
            ii += 3

        #print 'ii=', ii, 'indices_count=', indices_count
        #print 'iv=', iv, 'vertices_count', vertices_count

        self.batch.set_data(vertices, vertices_count, indices, indices_count)

        free(vertices)
        free(indices)



    property points:
        '''Property for getting/settings points of the line

        .. warning::

            This will always reconstruct the whole graphics from the new points
            list. It can be very CPU expensive.
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            self._points = list(points)
            self.flag_update()

    property dash_length:
        '''Property for getting/setting the length of the dashes in the curve

        .. versionadded:: 1.0.8
        '''
        def __get__(self):
            return self._dash_length

        def __set__(self, value):
            if value < 0:
                raise GraphicException('Invalid dash_length value, must be >= 0')
            self._dash_length = value
            self.flag_update()

    property dash_offset:
        '''Property for getting/setting the offset between the dashes in the curve

        .. versionadded:: 1.0.8
        '''
        def __get__(self):
            return self._dash_offset

        def __set__(self, value):
            if value < 0:
                raise GraphicException('Invalid dash_offset value, must be >= 0')
            self._dash_offset = value
            self.flag_update()

    property width:
        '''Determine the width of the line, default to 1.0.

        .. versionadded:: 1.4.1
        '''
        def __get__(self):
            return self._width

        def __set__(self, value):
            if value <= 0:
                raise GraphicException('Invalid width value, must be > 0')
            self._width = value
            self.flag_update()

    property cap:
        '''Determine the cap of the line, default to "round"

        .. versionadded:: 1.4.1
        '''
        def __get__(self):
            if self._cap == LINE_CAP_SQUARE:
                return 'square'
            elif self._cap == LINE_CAP_ROUND:
                return 'round'
            return 'none'

        def __set__(self, value):
            if value not in ('none', 'square', 'round'):
                raise GraphicException('Invalid cap, must be one of '
                        '"none", "square", "round"')
            if value == 'square':
                self._cap = LINE_CAP_SQUARE
            elif value == 'round':
                self._cap = LINE_CAP_ROUND
            else:
                self._cap = LINE_CAP_NONE
            self.flag_update()

    property joint:
        '''Determine the join of the line, default to "round"

        .. versionadded:: 1.4.1
        '''

        def __get__(self):
            if self._joint == LINE_JOINT_ROUND:
                return 'round'
            elif self._joint == LINE_JOINT_BEVEL:
                return 'bevel'
            elif self._joint == LINE_JOINT_MITER:
                return 'miter'
            return 'none'

        def __set__(self, value):
            if value not in ('none', 'miter', 'bevel', 'round'):
                raise GraphicException('Invalid joint, must be one of '
                    '"none", "miter", "bevel", "round"')
            if value == 'round':
                self._joint = LINE_JOINT_ROUND
            elif value == 'bevel':
                self._joint = LINE_JOINT_BEVEL
            elif value == 'miter':
                self._joint = LINE_JOINT_MITER
            else:
                self._joint = LINE_JOINT_NONE
            self.flag_update()

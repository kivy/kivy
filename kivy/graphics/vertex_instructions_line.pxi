DEF LINE_CAP_NONE = 0
DEF LINE_CAP_SQUARE = 1
DEF LINE_CAP_ROUND = 2

DEF LINE_JOINT_NONE = 0
DEF LINE_JOINT_MITER = 1
DEF LINE_JOINT_BEVEL = 2
DEF LINE_JOINT_ROUND = 3

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
        cdef int i, count = len(self.points) / 2
        cdef list p = self.points
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef float tex_x
        cdef char *buf = NULL
        cdef Texture texture = self.texture



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
            return None

        def __set__(self, value):
            if value not in (None, 'square', 'round'):
                raise GraphicException('Invalid cap, must be one of '
                        'None, "square", "round"')
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
            return None

        def __set__(self, value):
            if value not in (None, 'miter', 'bevel', 'round'):
                raise GraphicException('Invalid joint, must be one of '
                    'None, "miter", "bevel", "round"')
            if value == 'round':
                self._joint = LINE_JOINT_ROUND
            elif value == 'bevel':
                self._joint = LINE_JOINT_BEVEL
            elif value == 'miter':
                self._joint = LINE_JOINT_MITER
            else:
                self._joint = LINE_JOINT_NONE
            self.flag_update()

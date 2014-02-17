'''
SVG
===

Load an SVG as a graphics instruction
'''

include "common.pxi"

import re
from xml.etree.cElementTree import parse
from kivy.graphics.instructions cimport RenderContext
from kivy.graphics.vertex_instructions import Mesh

DEF BEZIER_POINTS = 64 # 10
DEF CIRCLE_POINTS = 64 # 24
DEF TOLERANCE = 0.001

from cython.operator cimport dereference as deref, preincrement as inc
cdef extern from "<vector>" namespace "std":
    cdef cppclass vector[T]:
        cppclass iterator:
            T operator*()
            iterator operator++()
            bint operator==(iterator)
            bint operator!=(iterator)
        vector()
        void push_back(T&)
        T& operator[](int)
        T& at(int)
        iterator begin()
        iterator end()

cdef extern from "../lib/poly2tri/poly2tri/poly2tri.h" namespace "p2t":
    cdef cppclass Point:
        double x
        double y
        Point(double x, double y)

    cdef cppclass Triangle:
        Triangle(Point &, Point &, Point &)
        Point *GetPoint(int &index)

    cdef cppclass CDT:
        CDT(vector[Point *] polyline)
        void Triangulate()
        vector[Triangle *] GetTriangles()


cdef str SVG_FS = '''
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 vertex_color;

void main (void) {
    gl_FragColor = vertex_color / 255.;
}
'''

cdef str SVG_VS = '''
#ifdef GL_ES
    precision highp float;
#endif

attribute vec2 v_pos;
attribute vec4 v_color;
uniform mat4 modelview_mat;
uniform mat4 projection_mat;
varying vec4 vertex_color;

void main (void) {
    vertex_color = v_color;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 0.0, 1.0);
}
'''

cdef dict colormap = {
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aqua': '#00ffff',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'black': '#000000',
    'blanchedalmond': '#ffebcd',
    'blue': '#0000ff',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgrey': '#a9a9a9',
    'darkgreen': '#006400',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'fuchsia': '#ff00ff',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'gray': '#808080',
    'grey': '#808080',
    'green': '#008000',
    'greenyellow': '#adff2f',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgreen': '#90ee90',
    'lightgray': '#d3d3d3',
    'lightgrey': '#d3d3d3',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'lime': '#00ff00',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'maroon': '#800000',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'navy': '#000080',
    'oldlace': '#fdf5e6',
    'olive': '#808000',
    'olivedrab': '#6b8e23',
    'orange': '#ffa500',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#db7093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'purple': '#800080',
    'red': '#ff0000',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'silver': '#c0c0c0',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'teal': '#008080',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'white': '#ffffff',
    'whitesmoke': '#f5f5f5',
    'yellow': '#ffff00',
    'yellowgreen': '#9acd32',
}


cdef set COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
cdef set UPPERCASE = set('MZLHVCSQTA')
cdef object RE_LIST = re.compile(
    r'([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)')
cdef object RE_COMMAND = re.compile(
    r'([MmZzLlHhVvCcSsQqTtAa])')
cdef object RE_FLOAT = re.compile(
    r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?')
cdef object RE_POLYLINE = re.compile(
    r'(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)')


def _tokenize_path(pathdef):
    for x in RE_COMMAND.split(pathdef):
        if x in COMMANDS:
            yield x
        for token in RE_FLOAT.findall(x):
            yield token

cdef float parse_float(txt):
    if txt[-2:] == 'px':
        return float(txt[:-2])
    return float(txt)

cdef list parse_list(string):
    return re.findall(RE_LIST, string)

cdef dict parse_style(string):
    cdef dict sdict = {}
    for item in string.split(';'):
        if ':' in item:
            key, value = item.split(':', 1)
            sdict[key] = value
    return sdict


cdef parse_color(c):
    cdef int r, g, b, a
    if c is None or c == 'none':
        return None
    if c[0] == '#':
        c = c[1:]
    if c[:5] == 'url(#':
        return c[5:-1]

    if str(c) in colormap:
        c = colormap[str(c)][1:]
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        a = 255
    elif len(c) == 8:
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        a = int(c[6:8], 16)
    elif len(c) == 6:
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        a = 255
    elif len(c) == 4:
        r = int(c[0], 16) * 17
        g = int(c[1], 16) * 17
        b = int(c[2], 16) * 17
        a = int(c[3], 16) * 17
    elif len(c) == 3:
        r = int(c[0], 16) * 17
        g = int(c[1], 16) * 17
        b = int(c[2], 16) * 17
        a = 255
    else:
        # ...
        raise Exception('Invalid color format {}'.format(c))
    return [r, g, b, a]


class Matrix(object):
    def __init__(self, string=None):
        self.values = [1, 0, 0, 1, 0, 0] #Identity matrix seems a sensible default
        if isinstance(string, str):
            if string.startswith('matrix('):
                self.values = [float(x) for x in parse_list(string[7:-1])]
            elif string.startswith('translate('):
                x, y = [float(x) for x in parse_list(string[10:-1])]
                self.values = [1, 0, 0, 1, x, y]
            elif string.startswith('scale('):
                sx, sy = [float(x) for x in parse_list(string[6:-1])]
                self.values = [sx, 0, 0, sy, 0, 0]
        elif string is not None:
            self.values = list(string)

    def __call__(self, other):
        return (self.values[0]*other[0] + self.values[2]*other[1] + self.values[4],
                self.values[1]*other[0] + self.values[3]*other[1] + self.values[5])

    def inverse(self):
        d = float(self.values[0]*self.values[3] - self.values[1]*self.values[2])
        return Matrix([self.values[3]/d, -self.values[1]/d, -self.values[2]/d, self.values[0]/d,
                       (self.values[2]*self.values[5] - self.values[3]*self.values[4])/d,
                       (self.values[1]*self.values[4] - self.values[0]*self.values[5])/d])

    def __mul__(self, other):
        a, b, c, d, e, f = self.values
        u, v, w, x, y, z = other.values
        return Matrix([a*u + c*v, b*u + d*v, a*w + c*x, b*w + d*x, a*y + c*z + e, b*y + d*z + f])


class GradientContainer(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.callback_dict = {}

    def call_me_on_add(self, callback, grad_id):
        '''The client wants to know when the gradient with id grad_id gets
        added.  So store this callback for when that happens.
        When the desired gradient is added, the callback will be called
        with the gradient as the first and only argument.
        '''
        cblist = self.callback_dict.get(grad_id, None)
        if cblist == None:
            cblist = [callback]
            self.callback_dict[grad_id] = cblist
            return
        cblist.append(callback)

    def update(self, *args, **kwargs):
        raise NotImplementedError('update not done for GradientContainer')

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        callbacks = self.callback_dict.get(key, [])
        for callback in callbacks:
            callback(val)


class Gradient(object):
    def __init__(self, element, svg):
        self.element = element
        self.stops = {}
        for e in element.getiterator():
            if e.tag.endswith('stop'):
                style = parse_style(e.get('style', ''))
                color = parse_color(e.get('stop-color'))
                if 'stop-color' in style:
                    color = parse_color(style['stop-color'])
                color[3] = int(float(e.get('stop-opacity', '1')) * 255)
                if 'stop-opacity' in style:
                    color[3] = int(float(style['stop-opacity']) * 255)
                self.stops[float(e.get('offset'))] = color
        self.stops = sorted(self.stops.items())
        self.svg = svg
        self.inv_transform = Matrix(element.get('gradientTransform')).inverse()

        inherit = self.element.get('{http://www.w3.org/1999/xlink}href')
        parent = None
        delay_params = False
        if inherit:
            parent_id = inherit[1:]
            parent = self.svg.gradients.get(parent_id, None)
            if parent == None:
                self.svg.gradients.call_me_on_add(self.tardy_gradient_parsed, parent_id)
                delay_params = True
                return
        if not delay_params:
            self.get_params(parent)

    def interp(self, pt):
        if not self.stops: return [255, 0, 255, 255]
        t = self.grad_value(self.inv_transform(pt))
        if t < self.stops[0][0]:
            return self.stops[0][1]
        for n, top in enumerate(self.stops[1:]):
            bottom = self.stops[n]
            if t <= top[0]:
                u = bottom[0]
                v = top[0]
                alpha = (t - u)/(v - u)
                return [int(x[0] * (1 - alpha) + x[1] * alpha) for x in zip(bottom[1], top[1])]
        return self.stops[-1][1]

    def get_params(self, parent):
        for param in self.params:
            v = None
            if parent:
                v = getattr(parent, param, None)
            my_v = self.element.get(param)
            if my_v:
                v = float(my_v)
            if v:
                setattr(self, param, v)

    def tardy_gradient_parsed(self, gradient):
        self.get_params(gradient)


class LinearGradient(Gradient):
    params = ['x1', 'x2', 'y1', 'y2', 'stops']

    def grad_value(self, pt):
        return ((pt[0] - self.x1)*(self.x2 - self.x1) + (pt[1] - self.y1)*(self.y2 - self.y1)) / ((self.x1 - self.x2)**2 + (self.y1 - self.y2)**2)


class RadialGradient(Gradient):
    params = ['cx', 'cy', 'r', 'stops']

    def grad_value(self, pt):
        return sqrt((pt[0] - self.cx) ** 2 + (pt[1] - self.cy) ** 2)/self.r


cdef class Svg(RenderContext):

    cdef:
        public double width
        public double height
        list paths
        object transform
        object fill
        object stroke
        float opacity
        float x
        float y
        int close_index
        list path
        list loop
        int bezier_points
        int circle_points
        public object gradients
        list bezier_coefficients
        float anchor_x
        float anchor_y
        double last_cx
        double last_cy

    def __init__(self, filename, anchor_x=0, anchor_y=0,
            bezier_points=BEZIER_POINTS, circle_points=CIRCLE_POINTS):
        '''Creates an SVG object from a .svg or .svgz file.

            `filename`: str
                The name of the file to be loaded.
            `anchor_x`: float
                The horizontal anchor position for scaling and rotations. Defaults to 0. The symbolic
                values 'left', 'center' and 'right' are also accepted.
            `anchor_y`: float
                The vertical anchor position for scaling and rotations. Defaults to 0. The symbolic
                values 'bottom', 'center' and 'top' are also accepted.
            `bezier_points`: int
                The number of line segments into which to subdivide Bezier splines. Defaults to 10.
            `circle_points`: int
                The number of line segments into which to subdivide circular and elliptic arcs.
                Defaults to 10.
        '''

        super(Svg, self).__init__(fs=SVG_FS, vs=SVG_VS,
                use_parent_projection=True, 
                use_parent_modelview=True)

        self.paths = []
        self.width = 0
        self.height = 0
        self.bezier_points = bezier_points
        self.circle_points = circle_points
        self.bezier_coefficients = []
        self.gradients = GradientContainer()
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

        self.filename = filename

    property anchor_x:

        def __set__(self, anchor_x):
            self._anchor_x = anchor_x
            if self._anchor_x == 'left':
                self._a_x = 0
            elif self._anchor_x == 'center':
                self._a_x = self.width * .5
            elif self._anchor_x == 'right':
                self._a_x = self.width
            else:
                self._a_x = self._anchor_x

        def __get__(self):
            return self._anchor_x


    property anchor_y:

        def __set__(self, anchor_y):
            self._anchor_y = anchor_y
            if self._anchor_y == 'bottom':
                self._a_y = 0
            elif self._anchor_y == 'center':
                self._a_y = self.height * .5
            elif self._anchor_y == 'top':
                self._a_y = self.height
            else:
                self._a_y = self.anchor_y

        def __get__(self):
            return self._anchor_y


    property filename:

        def __set__(self, filename):

            print 'loading', filename

            # check gzip
            with open(filename, 'rb') as fd:
                header = fd.read(3)

            if header == '\x1f\x8b\x08':
                import gzip
                fd = gzip.open(filename, 'rb')
            else:
                fd = open(filename, 'rb')

            try:
                tree = parse(fd)
            finally:
                fd.close()

            # parse tree
            self.parse_tree(tree)
            with self:
                self.render()

    def parse_tree(self, tree):
        root = tree._root
        self.paths = []
        self.width = parse_float(root.get('width', '0'))
        self.height = parse_float(root.get('height', '0'))
        if self.height:
            self.transform = Matrix([1, 0, 0, -1, 0, self.height])
        else:
            x, y, w, h = (parse_float(x) for x in parse_list(root.get('viewBox')))
            self.transform = Matrix([1, 0, 0, -1, -x, h + y])
            self.height = h
            self.width = w

        self.opacity = 1.0
        for e in root.getchildren():
            self.parse_element(e)

    def parse_element(self, e):
        self.fill = parse_color(e.get('fill'))
        self.stroke = parse_color(e.get('stroke'))
        oldopacity = self.opacity
        self.opacity *= float(e.get('opacity', 1))
        fill_opacity = float(e.get('fill-opacity', 1))
        stroke_opacity = float(e.get('stroke-opacity', 1))

        oldtransform = self.transform
        self.transform = self.transform * Matrix(e.get('transform'))

        style = e.get('style')
        if style:
            sdict = parse_style(style)
            if 'fill' in sdict:
                self.fill = parse_color(sdict['fill'])
            if 'fill-opacity' in sdict:
                fill_opacity *= float(sdict['fill-opacity'])
            if 'stroke' in sdict:
                self.stroke = parse_color(sdict['stroke'])
            if 'stroke-opacity' in sdict:
                stroke_opacity *= float(sdict['stroke-opacity'])

        if self.fill is None:
            self.fill = [0, 0, 0, 255]
        if self.stroke is None:
            self.stroke = [0, 0, 0, 0]
        if isinstance(self.stroke, list):
            self.stroke[3] = int(self.opacity * stroke_opacity * self.stroke[3])
        if isinstance(self.fill, list):
            self.fill[3] = int(self.opacity * fill_opacity * self.fill[3])
        if isinstance(self.stroke, list) and self.stroke[3] == 0:
            self.stroke = self.fill #Stroked edges antialias better

        if e.tag.endswith('path'):
            self.parse_path(e.get('d', ''))

        elif e.tag.endswith('rect'):
            x = 0
            y = 0
            if 'x' in e.keys():
                x = float(e.get('x'))
            if 'y' in e.keys():
                y = float(e.get('y'))
            h = float(e.get('height'))
            w = float(e.get('width'))
            self.new_path()
            self.set_position(x, y)
            self.set_position(x + w, y)
            self.set_position(x + w, y + h)
            self.set_position(x, y + h)
            self.set_position(x, y)
            self.end_path()

        elif e.tag.endswith('polyline') or e.tag.endswith('polygon'):
            pathdata = e.get('points')
            pathdata = re.findall(RE_POLYLINE, pathdata)
            pathdata.reverse()

            self.new_path()
            while pathdata:
                self.set_position(
                    float(pathdata.pop()),
                    float(pathdata.pop()))
            if e.tag.endswith('polygon'):
                self.close_path()
            self.end_path()

        elif e.tag.endswith('line'):
            x1 = float(e['x1'])
            y1 = float(e['y1'])
            x2 = float(e['x2'])
            y2 = float(e['y2'])
            self.new_path()
            self.set_position(x1, y1)
            self.set_position(x2, y2)
            self.end_path()

        elif e.tag.endswith('circle'):
            cx = float(e['cx'])
            cy = float(e['cy'])
            r = float(e['r'])
            self.new_path()
            for i in xrange(self.circle_points):
                theta = 2 * i * pi / self.circle_points
                self.set_position(cx + r * cos(theta), cy + r * sin(theta))
            self.close_path()
            self.end_path()

        elif e.tag.endswith('ellipse'):
            cx = float(e['cx'])
            cy = float(e['cy'])
            rx = float(e['rx'])
            ry = float(e['ry'])
            self.new_path()
            for i in xrange(self.circle_points):
                theta = 2 * i * pi / self.circle_points
                self.set_position(cx + rx * cos(theta), cy + ry * sin(theta))
            self.close_path()
            self.end_path()

        elif e.tag.endswith('linearGradient'):
            self.gradients[e.get('id')] = LinearGradient(e, self)

        elif e.tag.endswith('radialGradient'):
            self.gradients[e.get('id')] = RadialGradient(e, self)

        for c in e.getchildren():
            self.parse_element(c)

        self.transform = oldtransform
        self.opacity = oldopacity

    def parse_path(self, pathdef):
        # In the SVG specs, initial movetos are absolute, even if
        # specified as 'm'. This is the default behavior here as well.
        # But if you pass in a current_pos variable, the initial moveto
        # will be relative to that current_pos. This is useful.
        elements = list(_tokenize_path(pathdef))
        # Reverse for easy use of .pop()
        elements.reverse()

        sx = sy = None
        command = None

        self.new_path()

        while elements:

            if elements[-1] in COMMANDS:
                # New command.
                last_command = command # Used by S and T
                command = elements.pop()
                absolute = command in UPPERCASE
                command = command.upper()
            else:
                # If this element starts with numbers, it is an implicit command
                # and we don't change the command. Check that it's allowed:
                if command is None:
                    raise ValueError("Unallowed implicit command in %s, position %s" % (
                        pathdef, len(pathdef.split()) - len(elements)))


            if command == 'M':
                # Moveto command.
                x = float(elements.pop())
                y = float(elements.pop())
                self.set_position(x, y, absolute)

                if sx is None:
                    sx = self.x
                    sy = self.y

                # Implicit moveto commands are treated as lineto commands.
                # So we set command to lineto here, in case there are
                # further implicit commands after this moveto.
                command = 'L'

            elif command == 'Z':
                self.close_path()
                sx = sy = None

            elif command == 'L':
                x = float(elements.pop())
                y = float(elements.pop())
                self.set_position(x, y, absolute)

            elif command == 'H':
                x = float(elements.pop())
                if absolute:
                    self.set_position(x, self.y)
                else:
                    self.set_position(self.x + x, self.y)

            elif command == 'V':
                y = float(elements.pop())
                if absolute:
                    self.set_position(self.x, y)
                else:
                    self.set_position(self.x, self.y + y)

            elif command == 'C':
                c1x = float(elements.pop())
                c1y = float(elements.pop())
                c2x = float(elements.pop())
                c2y = float(elements.pop())
                endx = float(elements.pop())
                endy = float(elements.pop())

                if not absolute:
                    c1x += self.x
                    c1y += self.y
                    c2x += self.x
                    c2y += self.y
                    endx += self.x
                    endy += self.y

                self.curve_to(c1x, c1y, c2x, c2y, endx, endy)

            elif command == 'S':
                # Smooth curve. First control point is the "reflection" of
                # the second control point in the previous path.

                if last_command not in 'CS':
                    # If there is no previous command or if the previous command
                    # was not an C, c, S or s, assume the first control point is
                    # coincident with the current point.
                    c1x = self.x
                    c1y = self.y
                else:
                    # The first control point is assumed to be the reflection of
                    # the second control point on the previous command relative
                    # to the current point.
                    c1x = self.last_cx
                    c1y = self.last_cy

                c2x = float(elements.pop())
                c2y = float(elements.pop())
                endx = float(elements.pop())
                endy = float(elements.pop())

                if not absolute:
                    c2x += self.x
                    c2y += self.y
                    endx += self.x
                    endy += self.y

                self.curve_to(c1x, c1y, c2x, c2y, endx, endy)

            elif command == 'A':
                rx = float(elements.pop())
                ry = float(elements.pop())
                rotation = float(elements.pop())
                arc = float(elements.pop())
                sweep = float(elements.pop())            
                x = float(elements.pop())
                y = float(elements.pop())

                if not absolute:
                    x += self.x
                    y += self.y

                self.arc_to(rx, ry, rotation, arc, sweep, x, y)

            else:
                print 'Warning: unimplemented command {}'.format(command)

            '''
            elif command == 'Q':
                control = float(elements.pop()) + float(elements.pop()) * 1j
                end = float(elements.pop()) + float(elements.pop()) * 1j
                
                if not absolute:
                    control += current_pos
                    end += current_pos
                    
                segments.append(path.QuadraticBezier(current_pos, control, end))
                current_pos = end

            elif command == 'T':
                # Smooth curve. Control point is the "reflection" of
                # the second control point in the previous path.
                
                if last_command not in 'QT':
                    # If there is no previous command or if the previous command
                    # was not an Q, q, T or t, assume the first control point is
                    # coincident with the current point.
                    control = current_pos
                else:
                    # The control point is assumed to be the reflection of
                    # the control point on the previous command relative
                    # to the current point.
                    control = current_pos + current_pos - segments[-1].control2
                    
                end = float(elements.pop()) + float(elements.pop()) * 1j
                
                if not absolute:
                    control += current_pos
                    end += current_pos
                    
                segments.append(path.QuadraticBezier(current_pos, control, end))
                current_pos = end
            '''

        self.end_path()

    cdef void new_path(self):
        self.x = 0
        self.y = 0
        self.close_index = 0
        self.path = []
        self.loop = []

    cdef void close_path(self):
        self.loop.append(self.loop[0][:])
        self.path.append(self.loop)
        self.loop = []

    cdef void set_position(self, float x, float y, int absolute=1):
        if absolute:
            self.x = x
            self.y = y
        else:
            self.x += x
            self.y += y
        self.loop.append([x, y])

    def arc_to(self, float rx, float ry, float phi, float large_arc,
            float sweep, float x, float y):
        # This function is made out of magical fairy dust
        # http://www.w3.org/TR/2003/REC-SVG11-20030114/implnote.html#ArcImplementationNotes
        x1 = self.x
        y1 = self.y
        x2 = x
        y2 = y
        cp = cos(phi)
        sp = sin(phi)
        dx = .5 * (x1 - x2)
        dy = .5 * (y1 - y2)
        x_ = cp * dx + sp * dy
        y_ = -sp * dx + cp * dy
        r2 = (((rx * ry)**2 - (rx * y_)**2 - (ry * x_)**2)/
	      ((rx * y_)**2 + (ry * x_)**2))
        if r2 < 0: r2 = 0
        r = sqrt(r2)
        if large_arc == sweep:
            r = -r
        cx_ = r * rx * y_ / ry
        cy_ = -r * ry * x_ / rx
        cx = cp * cx_ - sp * cy_ + .5 * (x1 + x2)
        cy = sp * cx_ + cp * cy_ + .5 * (y1 + y2)
        def angle(u, v):
            a = acos((u[0]*v[0] + u[1]*v[1]) / sqrt((u[0]**2 + u[1]**2) * (v[0]**2 + v[1]**2)))
            sgn = 1 if u[0]*v[1] > u[1]*v[0] else -1
            return sgn * a

        psi = angle((1,0), ((x_ - cx_)/rx, (y_ - cy_)/ry))
        delta = angle(((x_ - cx_)/rx, (y_ - cy_)/ry),
                      ((-x_ - cx_)/rx, (-y_ - cy_)/ry))
        if sweep and delta < 0: delta += pi * 2
        if not sweep and delta > 0: delta -= pi * 2
        n_points = max(int(abs(self.circle_points * delta / (2 * pi))), 1)

        for i in xrange(n_points + 1):
            theta = psi + i * delta / n_points
            ct = cos(theta)
            st = sin(theta)
            self.set_position(cp * rx * ct - sp * ry * st + cx,
                    sp * rx * ct + cp * ry * st + cy)

    cdef void curve_to(self, float x1, float y1, float x2, float y2,
            float x, float y):
        if not self.bezier_coefficients:
            for i in xrange(self.bezier_points+1):
                t = float(i)/self.bezier_points
                t0 = (1 - t) ** 3
                t1 = 3 * t * (1 - t) ** 2
                t2 = 3 * t ** 2 * (1 - t)
                t3 = t ** 3
                self.bezier_coefficients.append([t0, t1, t2, t3])
        self.last_cx = x2
        self.last_cy = y2
        for i, t in enumerate(self.bezier_coefficients):
            px = t[0] * self.x + t[1] * x1 + t[2] * x2 + t[3] * x
            py = t[0] * self.y + t[1] * y1 + t[2] * y2 + t[3] * y
            self.loop.append([px, py])

        self.x, self.y = px, py

    cdef void end_path(self):
        self.path.append(self.loop)

        path = []
        for orig_loop in self.path:

            if not orig_loop:
                continue

            loop = [orig_loop[0]]
            for pt in orig_loop:
                if (pt[0] - loop[-1][0]) ** 2 + (pt[1] - loop[-1][1]) ** 2 > TOLERANCE:
                    if pt not in loop:
                        loop.append(pt)
            path.append(loop)

        self.paths.append((
            path if self.stroke else None,
            self.stroke,
            self.triangulate(path) if self.fill else None,
            self.fill,
            self.transform))

        self.path = []

    def triangulate(self, looplist):
        cdef CDT *cdt
        cdef Point *p
        cdef Triangle *t
        cdef vector[Point *] *polyline
        cdef vector[Triangle *].iterator it
        cdef vector[Triangle *] triangles

        #print 'triangulate()'
        #return []

        tris = []
        for points in looplist:

            polyline = new vector[Point *]()
            if points[0] == points[-1]:
                points = points[:-1]
            for x, y in points:
                p = new Point(x, y)
                polyline.push_back(p)

            cdt = new CDT(polyline[0])
            cdt.Triangulate()
            triangles = cdt.GetTriangles()

            it = triangles.begin()
            while it != triangles.end():
                t = deref(it)
                tris.append([t.GetPoint(0).x, t.GetPoint(0).y])
                tris.append([t.GetPoint(1).x, t.GetPoint(1).y])
                tris.append([t.GetPoint(2).x, t.GetPoint(2).y])
                inc(it)

            del cdt
            del polyline

        return tris

    def render(self):
        vertex_format = [
            ('v_pos', 2, 'float'),
            ('v_color', 4, 'float')]

        for path, stroke, tris, fill, transform in self.paths:

            if tris:
                if isinstance(fill, str):
                    g = self.gradients[fill]
                    fills = [g.interp(x) for x in tris]
                else:
                    fills = [fill for x in tris]
                indices = range(len(tris))
                vertices = []
                for vtx, clr in zip(tris, fills):
                    vtx = transform(vtx)
                    vertices += [vtx[0], vtx[1], clr[0], clr[1], clr[2], clr[3]]

                mesh = Mesh(fmt=vertex_format,
                    indices=indices, vertices=vertices,
                    mode='triangles')

            if path:
                for loop in path:
                    loop_plus = []
                    for i in xrange(len(loop) - 1):
                        loop_plus += [loop[i], loop[i+1]]
                    if isinstance(stroke, str):
                        g = self.gradients[stroke]
                        strokes = [g.interp(x) for x in loop_plus]
                    else:
                        strokes = [stroke for x in loop_plus]

                    vertices = []
                    indices = range(len(strokes))
                    for vtx, clr in zip(loop_plus, strokes):
                        vtx = transform(vtx)
                        vertices += [vtx[0], vtx[1], clr[0], clr[1], clr[2], clr[3]]

                    print 'add a mesh', len(indices), len(vertices)
                    mesh = Mesh(
                        fmt=vertex_format,
                        indices=indices,
                        vertices=vertices,
                        mode='lines')

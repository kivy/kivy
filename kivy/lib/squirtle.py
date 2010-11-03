'''Squirtle mini-library for SVG rendering in Pyglet.

Example usage:
    import squirtle
    my_svg = squirtle.SVG('filename.svg')
    my_svg.draw(100, 200, angle=15)

'''

__all__ = ('SVG', 'setup_gl')

from kivy.core.gl import GL_BLEND, GL_LINE_SMOOTH, GL_SRC_ALPHA, \
        GL_ONE_MINUS_SRC_ALPHA, GL_COMPILE, GL_TRIANGLES, GL_LINES, \
        GL_TRIANGLE_FAN, GL_TRIANGLE_STRIP, \
        glEnable, glGenLists, glNewList, glEndList, glPushMatrix, \
        glPopMatrix, glTranslatef, glRotatef, glScalef, glCallList, \
        glBegin, glEnd, glColor4ub, glVertex3f, glBlendFunc, \
        GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_NONZERO, \
        GLU_TESS_VERTEX, GLU_TESS_BEGIN, GLU_TESS_END, GLU_TESS_ERROR, \
        GLU_TESS_COMBINE, \
        gluTessNormal, gluTessProperty, gluNewTess, gluTessCallback, \
        gluTessBeginContour, gluTessEndContour, gluTessBeginPolygon, \
        gluTessEndPolygon, gluTessVertex, gluErrorString

from xml.etree.cElementTree import parse
import re
import math
try:
    # get the faster one
    from cStringIO import StringIO
except ImportError:
    # fallback to the default one
    from StringIO import StringIO
from kivy.logger import Logger

BEZIER_POINTS = 10
CIRCLE_POINTS = 24
TOLERANCE = 0.001
def setup_gl():
    """Set various pieces of OpenGL state for better rendering of SVG.

    """
    
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def parse_list(string):
    return re.findall("([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", string)

def parse_style(string):
    sdict = {}
    for item in string.split(';'):
        if ':' in item:
            key, value = item.split(':')
            sdict[key] = value
    return sdict

colormap = {
    # X11 colour table (from "CSS3 module: Color working draft"), with
    # gray/grey spelling issues fixed.  This is a superset of HTML 4.0
    # colour names used in CSS 1.
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


def parse_color(c, default=None):
    if not c:
        return default
    if c == 'none':
        return None
    if c[0] == '#': c = c[1:]
    if c.startswith('url(#'):
        return c[5:-1]
    try:
        if str(c) in colormap:
            c = colormap[str(c)][1:]
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
        elif len(c) == 6:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
        elif len(c) == 3:
            r = int(c[0], 16) * 17
            g = int(c[1], 16) * 17
            b = int(c[2], 16) * 17
        else:
            Logger.exception('Squirtle: incorrect length for color %s' % str(c))
        return [r, g, b, 255]
    except Exception, ex:
        Logger.exception('Squirtle: exception parsing color %s' % str(c))
        return None

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

class TriangulationError(Exception):
    """Exception raised when triangulation of a filled area fails. For internal use only.

    """
    pass

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
        return math.sqrt((pt[0] - self.cx) ** 2 + (pt[1] - self.cy) ** 2)/self.r

class SVG(object):
    """Opaque SVG image object.

    Users should instantiate this object once for each SVG file they wish to
    render.

    """

    _tess = None
    _disp_list_cache = {}
    def __init__(self, filename, anchor_x=0, anchor_y=0, bezier_points=BEZIER_POINTS, circle_points=CIRCLE_POINTS, rawdata=None):
        """Creates an SVG object from a .svg or .svgz file.

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
            `rawdata`: string
                Raw data string (you need to set a fake filename for cache anyway)
                Defaults to None.
        """
        self._tess = gluNewTess()
        gluTessNormal(self._tess, 0, 0, 1)
        gluTessProperty(self._tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_NONZERO)

        self.filename = filename
        self.rawdata = rawdata
        self.bezier_points = bezier_points
        self.circle_points = circle_points
        self.bezier_coefficients = []
        self.gradients = GradientContainer()
        self.generate_disp_list()
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

    def _set_anchor_x(self, anchor_x):
        self._anchor_x = anchor_x
        if self._anchor_x == 'left':
            self._a_x = 0
        elif self._anchor_x == 'center':
            self._a_x = self.width * .5
        elif self._anchor_x == 'right':
            self._a_x = self.width
        else:
            self._a_x = self._anchor_x

    def _get_anchor_x(self):
        return self._anchor_x

    anchor_x = property(_get_anchor_x, _set_anchor_x)

    def _set_anchor_y(self, anchor_y):
        self._anchor_y = anchor_y
        if self._anchor_y == 'bottom':
            self._a_y = 0
        elif self._anchor_y == 'center':
            self._a_y = self.height * .5
        elif self._anchor_y == 'top':
            self._a_y = self.height
        else:
            self._a_y = self.anchor_y

    def _get_anchor_y(self):
        return self._anchor_y

    anchor_y = property(_get_anchor_y, _set_anchor_y)

    def generate_disp_list(self):
        if (self.filename, self.bezier_points) in self._disp_list_cache:
            self.disp_list, self.width, self.height = self._disp_list_cache[self.filename, self.bezier_points]
        else:
            if self.rawdata != None:
                f = StringIO(self.rawdata)
            else:
                if open(self.filename, 'rb').read(3) == '\x1f\x8b\x08': #gzip magic numbers
                    import gzip
                    f = gzip.open(self.filename, 'rb')
                else:
                    f = open(self.filename, 'rb')
            self.tree = parse(f)
            self.parse_doc()
            self.disp_list = glGenLists(1)
            glNewList(self.disp_list, GL_COMPILE)
            self.render_slowly()
            glEndList()
            self._disp_list_cache[self.filename, self.bezier_points] = (self.disp_list, self.width, self.height)

    def draw(self, x, y, z=0, angle=0, scale=1):
        """Draws the SVG to screen.

        :Parameters
            `x` : float
                The x-coordinate at which to draw.
            `y` : float
                The y-coordinate at which to draw.
            `z` : float
                The z-coordinate at which to draw. Defaults to 0. Note that z-ordering may not
                give expected results when transparency is used.
            `angle` : float
                The angle by which the image should be rotated (in degrees). Defaults to 0.
            `scale` : float
                The amount by which the image should be scaled, either as a float, or a tuple
                of two floats (xscale, yscale).

        """
        glPushMatrix()
        glTranslatef(x, y, z)
        if angle:
            glRotatef(angle, 0, 0, 1)
        if scale != 1:
            try:
                glScalef(scale[0], scale[1], 1)
            except TypeError:
                glScalef(scale, scale, 1)
        if self._a_x or self._a_y:
            glTranslatef(-self._a_x, -self._a_y, 0)
        glCallList(self.disp_list)
        glPopMatrix()

    def render_slowly(self):
        self.n_tris = 0
        self.n_lines = 0
        for path, stroke, tris, fill, transform in self.paths:
            if tris:
                self.n_tris += len(tris)/3
                if isinstance(fill, str):
                    g = self.gradients[fill]
                    fills = [g.interp(x) for x in tris]
                else:
                    fills = [fill for x in tris]
                #pyglet.graphics.draw(len(tris), GL_TRIANGLES,
                #                     ('v3f', sum((x + [0] for x in tris), [])),
                #                     ('c3B', sum(fills, [])))
                glBegin(GL_TRIANGLES)
                for vtx, clr in zip(tris, fills):
                    vtx = transform(vtx)
                    glColor4ub(*clr)
                    glVertex3f(vtx[0], vtx[1], 0)
                glEnd()
            if path:
                for loop in path:
                    self.n_lines += len(loop) - 1
                    loop_plus = []
                    for i in xrange(len(loop) - 1):
                        loop_plus += [loop[i], loop[i+1]]
                    if isinstance(stroke, str):
                        g = self.gradients[stroke]
                        strokes = [g.interp(x) for x in loop_plus]
                    else:
                        strokes = [stroke for x in loop_plus]
                    #pyglet.graphics.draw(len(loop_plus), GL_LINES,
                    #                     ('v3f', sum((x + [0] for x in loop_plus), [])),
                    #                     ('c3B', sum((stroke for x in loop_plus), [])))
                    glBegin(GL_LINES)
                    for vtx, clr in zip(loop_plus, strokes):
                        vtx = transform(vtx)
                        glColor4ub(*clr)
                        glVertex3f(vtx[0], vtx[1], 0)
                    glEnd()
    def parse_float(self, txt):
        if txt.endswith('px'):
            return float(txt[:-2])
        else:
            return float(txt)


    def parse_doc(self):
        self.paths = []
        self.width = self.parse_float(self.tree._root.get("width", '0'))
        self.height = self.parse_float(self.tree._root.get("height", '0'))
        if self.height:
            self.transform = Matrix([1, 0, 0, -1, 0, self.height])
        else:
            x, y, w, h = (self.parse_float(x) for x in parse_list(self.tree._root.get("viewBox")))
            self.transform = Matrix([1, 0, 0, -1, -x, h + y])
            self.height = h
            self.width = w
        self.opacity = 1.0
        for e in self.tree._root.getchildren():
            try:
                self.parse_element(e)
            except Exception, ex:
                Logger.exception('Squirtle: exception while parsing element %s' % e)
                raise

    def parse_element(self, e):
        default = object()
        self.fill = parse_color(e.get('fill'), default)
        self.stroke = parse_color(e.get('stroke'), default)
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
        if self.fill == default:
            self.fill = [0, 0, 0, 255]
        if self.stroke == default:
            self.stroke = [0, 0, 0, 0]
        if isinstance(self.stroke, list):
            self.stroke[3] = int(self.opacity * stroke_opacity * self.stroke[3])
        if isinstance(self.fill, list):
            self.fill[3] = int(self.opacity * fill_opacity * self.fill[3])
        if isinstance(self.stroke, list) and self.stroke[3] == 0: self.stroke = self.fill #Stroked edges antialias better

        if e.tag.endswith('path'):
            pathdata = e.get('d', '')
            pathdata = re.findall("([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", pathdata)

            def pnext():
                return (float(pathdata.pop(0)), float(pathdata.pop(0)))

            self.new_path()
            while pathdata:
                opcode = pathdata.pop(0)
                if opcode == 'M':
                    self.set_position(*pnext())
                elif opcode == 'C':
                    self.curve_to(*(pnext() + pnext() + pnext()))
                elif opcode == 'c':
                    mx = self.x
                    my = self.y
                    x1, y1 = pnext()
                    x2, y2 = pnext()
                    x, y = pnext()

                    self.curve_to(mx + x1, my + y1, mx + x2, my + y2, mx + x, my + y)
                elif opcode == 'S':
                    self.curve_to(2 * self.x - self.last_cx, 2 * self.y - self.last_cy, *(pnext() + pnext()))
                elif opcode == 's':
                    mx = self.x
                    my = self.y
                    x1, y1 = 2 * self.x - self.last_cx, 2 * self.y - self.last_cy
                    x2, y2 = pnext()
                    x, y = pnext()

                    self.curve_to(x1, y1, mx + x2, my + y2, mx + x, my + y)
                elif opcode == 'A':
                    rx, ry = pnext()
                    phi = float(pathdata.pop(0))
                    large_arc = int(pathdata.pop(0))
                    sweep = int(pathdata.pop(0))
                    x, y = pnext()
                    self.arc_to(rx, ry, phi, large_arc, sweep, x, y)
                elif opcode in 'zZ':
                    self.close_path()
                elif opcode == 'L':
                    self.line_to(*pnext())
                elif opcode == 'l':
                    x, y = pnext()
                    self.line_to(self.x + x, self.y + y)
                elif opcode == 'H':
                    x = float(pathdata.pop(0))
                    self.line_to(x, self.y)
                elif opcode == 'h':
                    x = float(pathdata.pop(0))
                    self.line_to(self.x + x, self.y)
                elif opcode == 'V':
                    y = float(pathdata.pop(0))
                    self.line_to(self.x, y)
                elif opcode == 'v':
                    y = float(pathdata.pop(0))
                    self.line_to(self.x, self.y + y)
                else:
                    self.warn("Unrecognised opcode: " + opcode)
            self.end_path()
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
            self.line_to(x+w,y)
            self.line_to(x+w,y+h)
            self.line_to(x,y+h)
            self.line_to(x,y)
            self.end_path()
        elif e.tag.endswith('polyline') or e.tag.endswith('polygon'):
            pathdata = e.get('points')
            pathdata = re.findall("(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", pathdata)
            def pnext():
                return (float(pathdata.pop(0)), float(pathdata.pop(0)))
            self.new_path()
            while pathdata:
                self.line_to(*pnext())
            if e.tag.endswith('polygon'):
                self.close_path()
            self.end_path()
        elif e.tag.endswith('line'):
            x1 = float(e.get('x1'))
            y1 = float(e.get('y1'))
            x2 = float(e.get('x2'))
            y2 = float(e.get('y2'))
            self.new_path()
            self.set_position(x1, y1)
            self.line_to(x2, y2)
            self.end_path()
        elif e.tag.endswith('circle'):
            cx = float(e.get('cx'))
            cy = float(e.get('cy'))
            r = float(e.get('r'))
            self.new_path()
            for i in xrange(self.circle_points):
                theta = 2 * i * math.pi / self.circle_points
                self.line_to(cx + r * math.cos(theta), cy + r * math.sin(theta))
            self.close_path()
            self.end_path()
        elif e.tag.endswith('ellipse'):
            cx = float(e.get('cx'))
            cy = float(e.get('cy'))
            rx = float(e.get('rx'))
            ry = float(e.get('ry'))
            self.new_path()
            for i in xrange(self.circle_points):
                theta = 2 * i * math.pi / self.circle_points
                self.line_to(cx + rx * math.cos(theta), cy + ry * math.sin(theta))
            self.close_path()
            self.end_path()
        elif e.tag.endswith('linearGradient'):
            self.gradients[e.get('id')] = LinearGradient(e, self)
        elif e.tag.endswith('radialGradient'):
            self.gradients[e.get('id')] = RadialGradient(e, self)
        for c in e.getchildren():
            try:
                self.parse_element(c)
            except Exception, ex:
                Logger.exception('Squirtle: exception while parsing element %s' % c)
                raise
        self.transform = oldtransform
        self.opacity = oldopacity

    def new_path(self):
        self.x = 0
        self.y = 0
        self.close_index = 0
        self.path = []
        self.loop = []
    def close_path(self):
        self.loop.append(self.loop[0][:])
        self.path.append(self.loop)
        self.loop = []
    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.loop.append([x,y])

    def arc_to(self, rx, ry, phi, large_arc, sweep, x, y):
        # This function is made out of magical fairy dust
        # http://www.w3.org/TR/2003/REC-SVG11-20030114/implnote.html#ArcImplementationNotes
        x1 = self.x
        y1 = self.y
        x2 = x
        y2 = y
        cp = math.cos(phi)
        sp = math.sin(phi)
        dx = .5 * (x1 - x2)
        dy = .5 * (y1 - y2)
        x_ = cp * dx + sp * dy
        y_ = -sp * dx + cp * dy
        r2 = (((rx * ry)**2 - (rx * y_)**2 - (ry * x_)**2)/
	      ((rx * y_)**2 + (ry * x_)**2))
        if r2 < 0: r2 = 0
        r = math.sqrt(r2)
        if large_arc == sweep:
            r = -r
        cx_ = r * rx * y_ / ry
        cy_ = -r * ry * x_ / rx
        cx = cp * cx_ - sp * cy_ + .5 * (x1 + x2)
        cy = sp * cx_ + cp * cy_ + .5 * (y1 + y2)
        def angle(u, v):
            a = math.acos((u[0]*v[0] + u[1]*v[1]) / math.sqrt((u[0]**2 + u[1]**2) * (v[0]**2 + v[1]**2)))
            sgn = 1 if u[0]*v[1] > u[1]*v[0] else -1
            return sgn * a

        psi = angle((1,0), ((x_ - cx_)/rx, (y_ - cy_)/ry))
        delta = angle(((x_ - cx_)/rx, (y_ - cy_)/ry),
                      ((-x_ - cx_)/rx, (-y_ - cy_)/ry))
        if sweep and delta < 0: delta += math.pi * 2
        if not sweep and delta > 0: delta -= math.pi * 2
        n_points = max(int(abs(self.circle_points * delta / (2 * math.pi))), 1)

        for i in xrange(n_points + 1):
            theta = psi + i * delta / n_points
            ct = math.cos(theta)
            st = math.sin(theta)
            self.line_to(cp * rx * ct - sp * ry * st + cx,
                         sp * rx * ct + cp * ry * st + cy)

    def curve_to(self, x1, y1, x2, y2, x, y):
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

    def line_to(self, x, y):
        self.set_position(x, y)

    def end_path(self):
        self.path.append(self.loop)
        if self.path:
            path = []
            for orig_loop in self.path:
                if not orig_loop: continue
                loop = [orig_loop[0]]
                for pt in orig_loop:
                    if (pt[0] - loop[-1][0])**2 + (pt[1] - loop[-1][1])**2 > TOLERANCE:
                        loop.append(pt)
                path.append(loop)
            self.paths.append((path if self.stroke else None, self.stroke,
                               self.triangulate(path) if self.fill else None, self.fill,
                               self.transform))
        self.path = []

    def triangulate(self, looplist):
        tlist = []
        self.curr_shape = []

        def vertexCallback(vertex):
            self.curr_shape.append(list(vertex[0:2]))

        def beginCallback(which):
            self.tess_style = which

        def endCallback():
            if self.tess_style == GL_TRIANGLE_FAN:
                c = self.curr_shape.pop(0)
                p1 = self.curr_shape.pop(0)
                while self.curr_shape:
                    p2 = self.curr_shape.pop(0)
                    tlist.extend([c, p1, p2])
                    p1 = p2
            elif self.tess_style == GL_TRIANGLE_STRIP:
                p1 = self.curr_shape.pop(0)
                p2 = self.curr_shape.pop(0)
                while self.curr_shape:
                    p3 = self.curr_shape.pop(0)
                    tlist.extend([p1, p2, p3])
                    p1 = p2
                    p2 = p3
            elif self.tess_style == GL_TRIANGLES:
                tlist.extend(self.curr_shape)
            else:
                Logger.warning('Squirtle: Unrecognised tesselation style: %d' % (self.tess_style,))
            self.tess_style = None
            self.curr_shape = []

        def errorCallback(code):
            err = gluErrorString(code)
            Logger.warning('Squirtle: GLU Tesselation Error: ' + err)

        def combineCallback(coords, vertex_data, weights):
            return (coords[0], coords[1], coords[2])

        gluTessCallback(self._tess, GLU_TESS_VERTEX, vertexCallback)
        gluTessCallback(self._tess, GLU_TESS_BEGIN, beginCallback)
        gluTessCallback(self._tess, GLU_TESS_END, endCallback)
        gluTessCallback(self._tess, GLU_TESS_ERROR, errorCallback)
        gluTessCallback(self._tess, GLU_TESS_COMBINE, combineCallback)

        data_lists = []
        for vlist in looplist:
            d_list = []
            for x, y in vlist:
                v_data = (x, y, 0)
                found = False
                for x2, y2, z2 in d_list:
                    d = math.sqrt((x - x2) ** 2 + (y - y2) ** 2)
                    if d < 0.0000001:
                        # XXX we've found a coordinate nearly the same as an other
                        # coordinate. this is the "COMBINE" case of GLU tesslation
                        # But on my PyOpenGL version, i got the "need combine
                        # callback" error, and i'm unable to get ride of it until
                        # the wrong vertex is removed.
                        found = True
                        break
                if found:
                    continue
                d_list.append(v_data)
            data_lists.append(d_list)
        gluTessBeginPolygon(self._tess, None)
        for d_list in data_lists:
            gluTessBeginContour(self._tess)
            for v_data in reversed(d_list):
                gluTessVertex(self._tess, v_data, v_data)
            gluTessEndContour(self._tess)
        gluTessEndPolygon(self._tess)
        return tlist

    def warn(self, message):
        Logger.warning('Squirtle: svg parser on %s: %s' % (self.filename, message))

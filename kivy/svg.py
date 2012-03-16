import re
import math
from pprint import pprint
from xml.etree.cElementTree import parse

from kivy.logger import Logger


BEZIER_POINTS = 10
CIRCLE_POINTS = 24
TOLERANCE = 0.001


def parse_float(txt):
    if txt.endswith('px'):
        return float(txt[:-2])
    else:
        return float(txt)


def parse_list(string):
    return re.findall("([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", string)


def parse_style(string):
    sdict = {}
    for item in string.split(';'):
        if ':' in item:
            key, value = item.split(':')
            sdict[key] = value
    return sdict


class Matrix(object):

    def __init__(self, string=None):
        # Identity matrix seems a sensible default
        self.values = vals = [1, 0, 0, 1, 0, 0]
        if isinstance(string, str):
            if string.startswith('matrix('):
                vals = [float(x) for x in parse_list(string[7:-1])]
            elif string.startswith('translate('):
                x, y = [float(x) for x in parse_list(string[10:-1])]
                vals = [1, 0, 0, 1, x, y]
            elif string.startswith('scale('):
                sx, sy = [float(x) for x in parse_list(string[6:-1])]
                vals = [sx, 0, 0, sy, 0, 0]
        elif string is not None:
            vals = list(string)
        self.values = vals

    def __call__(self, other):
        vals = self.values
        return (vals[0] * other[0] + vals[2] * other[1] + vals[4],
                vals[1] * other[0] + vals[3] * other[1] + vals[5])

    def inverse(self):
        vals = self.values
        d = float(vals[0] * vals[3] - vals[1] * vals[2])
        return Matrix([vals[3] / d, - vals[1] / d, - vals[2] / d, vals[0] / d,
                      (vals[2] * vals[5] - vals[3] * vals[4]) / d,
                      (vals[1] * vals[4] - vals[0] * vals[5]) / d])

    def __mul__(self, other):
        a, b, c, d, e, f = self.values
        u, v, w, x, y, z = other.values
        return Matrix([a * u + c * v, b * u + d * v, a * w + c * x,
                       b * w + d * x, a * y + c * z + e, b * y + d * z + f])


class SVGData(object):

    def __init__(self, filename):
        """Creates an SVG object from a .svg or .svgz file.

            `filename`: str
                The name of the file to be loaded.
            `bezier_points`: int
                The number of line segments into which to subdivide Bezier
                splines.
                Defaults to 10.
            `circle_points`: int
                The number of line segments into which to subdivide circular
                and elliptic arcs.
                Defaults to 10.
            `rawdata`: string
                Raw data string (need to set a fake filename for cache anyway)
                Defaults to None.
        """
        self.width = -1
        self.height = -1

        self.bezier_points = BEZIER_POINTS
        self.circle_points = CIRCLE_POINTS
        self.bezier_coefficients = []

        self.filename = filename
        # gzip magic numbers
        if open(self.filename, 'rb').read(3) == '\x1f\x8b\x08':
            import gzip
            f = gzip.open(self.filename, 'rb')
        else:
            f = open(self.filename, 'rb')
        self.tree = parse(f)
        self.parse_doc()

    @property
    def size(self):
        return (self, self.width, self.height)

    def parse_doc(self):
        self.paths = []
        self.width = parse_float(self.tree._root.get("width", '0'))
        self.height = parse_float(self.tree._root.get("height", '0'))
        if self.height:
            self.transform = Matrix([1, 0, 0, -1, 0, self.height])
        else:
            r = self.tree._root
            x, y, w, h = (parse_float(x) for x in parse_list(r.get("viewBox")))
            self.transform = Matrix([1, 0, 0, -1, -x, h + y])
            self.height = h
            self.width = w
        for e in self.tree._root.getchildren():
            try:
                self.parse_element(e)
            except:
                Logger.exception('SVGData: Error while parsing element %s' % e)
                raise

    def parse_element(self, e):
        oldtransform = self.transform
        self.transform = self.transform * Matrix(e.get('transform'))

        if e.tag.endswith('path'):
            pathdata = e.get('d', '')
            regex = "([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)"
            pathdata = re.findall(regex, pathdata)

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

                    self.curve_to(mx + x1, my + y1,
                                  mx + x2, my + y2,
                                  mx + x, my + y)
                elif opcode == 'S':
                    self.curve_to(2 * self.x - self.last_cx,
                        2 * self.y - self.last_cy, *(pnext() + pnext()))
                elif opcode == 's':
                    mx = self.x
                    my = self.y
                    x1 = 2 * self.x - self.last_cx
                    y1 = 2 * self.y - self.last_cy
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
                    Logger.warn("SVGData: Unrecognised opcode: " + opcode)
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
            self.line_to(x + w, y)
            self.line_to(x + w, y + h)
            self.line_to(x, y + h)
            self.line_to(x, y)
            self.end_path()

        elif e.tag.endswith('polyline') or e.tag.endswith('polygon'):
            pathdata = e.get('points')
            regex = "(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)"
            pathdata = re.findall(regex, pathdata)

            def pnext2():
                return (float(pathdata.pop(0)), float(pathdata.pop(0)))

            self.new_path()
            while pathdata:
                self.line_to(*pnext2())
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
                self.line_to(cx + rx * math.cos(theta),
                             cy + ry * math.sin(theta))
            self.close_path()
            self.end_path()

        #elif e.tag.endswith('linearGradient'):
        #    self.gradients[e.get('id')] = LinearGradient(e, self)

        #elif e.tag.endswith('radialGradient'):
        #    self.gradients[e.get('id')] = RadialGradient(e, self)

        for c in e.getchildren():
            try:
                self.parse_element(c)
            except:
                err = 'SVGData: Exception while parsing child element ' \
                      '%s of %s' % (c, e)
                Logger.exception(err)
                raise

        #done parsing element, restore transform
        self.transform = oldtransform

    def new_path(self):
        self.x = 0
        self.y = 0
        self.close_index = 0
        self.path = []
        self.loop = []
        print "new path"

    def close_path(self):
        self.loop.append(self.loop[0][:])
        self.path.append(self.loop)
        self.loop = []
        print "close path"

    def set_position(self, x, y):
        print "set position", x, y
        self.x = x
        self.y = y
        self.loop.append([x, y])

    def curve_to(self, x1, y1, x2, y2, x, y):
        print "curve to:", x1, y1, x2, y2, x, y
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
        print "line to", x, y
        self.set_position(x, y)

    def end_path(self):
        print "end path"
        self.path.append(self.loop)
        if self.path:
            path = []
            for orig_loop in self.path:
                if not orig_loop:
                    continue
                loop = [orig_loop[0]]
                for pt in orig_loop:
                    val = (pt[0] - loop[-1][0])**2 + (pt[1] - loop[-1][1])**2
                    if val > TOLERANCE:
                        loop.append(pt)
                path.append(loop)

            print "path: "
            pprint(path)
            print "loop: "
            pprint(self.loop)

        self.path = []


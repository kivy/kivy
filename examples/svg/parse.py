from  xml.dom.minidom import parse
from pprint import pprint

doc = parse('test.svg') 
root = doc.documentElement

path    = root.getElementsByTagName("path")[0]
attribs = dict(path.attributes.items())

svg_data = attribs['d']
path = []


state = {}
origin = (0,0)
position = None
for command in svg_data.split(' '):

    if command.isalpha():
        if command.isupper():
            origin = (0,0)
        else:
            origin = position

    if command == 'M':
        PathStart()
        state['command'] = PathLineTo

    elif command == 'c':
        state['command'] = "PathLineTo" #"PathRCubicTo"

    elif command == 'z':
        path.append('PathClose')

    else:
        pos = map(float, command.split(','))
        position = pos[0]+origin[0], pos[1]+origin[1]
        path.append( state['command']+ str(position))


for instr in path:
    print instr


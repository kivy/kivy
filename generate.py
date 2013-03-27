from json import load
from sys import argv
from cgi import escape

HTML_HEADER = '''
<!doctype html>
<html>
<style type="text/css">
body {
    font-family: monospace;
}

.style1 div.block {
    background-color: #676767;
    min-height: 20px;
    clear: right;
}

.style1 div span {
    position: absolute;
    display: none;
}

.style1 div.line {
    margin-top: 1px;
}

.style1 div.line-mainloop {
    margin-top: 20px;
}

.style1 div.line-header {
    width: 150px;
    float: left;
}

.style1 div.line-time {
    width: 100px;
    float: left;
}

.style1 div.line-content {
    margin-left: 250px;
}

.style1 div.alert div.line-time {
    color: #EE4444;
}

/** SUMMARY STYLE **/
.style2 div.block {
    float: left;
    height: 5px;
    margin-left: 0px !important;
    left: 0px;
}

.style2 div.mainloop,
.style2 div span,
.style2 div.line-time,
.style2 div.line-header {
    display: none; 
}

.style2 div.frame {
    display: block;
    float: none;
    clear: both;
    height: 5px;
    width: 9000px;
}

.style2 div.frametime {
    position: fixed;
    top: 0px;
    left: 0px;
    width: 700px;
    height: 100%;
    border-right: 1px solid #000000;
}

/** SECTION COLOR **/
div.block {
    background-color: #676767;
}

div.clock-tick, div.clock-sleep, div.dispatch-input, div.clock-tick-draw {
    background-color: #44EE44;
}

div.draw {
    background-color: #4444EE;
}
div.flip {
    background-color: #ee4444;
}
</style>
<body class="style2">
'''

HTML_FOOTER = '''
<div class="frametime"></div>
</body>
</html>
'''

WIDTH = 700

def generate(fn):
    with open(fn) as fd:
        events = load(fd)

    # extract event per frame
    html = []
    tags = {}
    start_mainloop = 0
    for infos in events:
        time, event = infos[:2]

        # extract a main event
        if event == 'start-mainloop':
            start_mainloop = time
            index_mainloop = len(html)
            html.append('')
        elif event == 'end-mainloop':
            html[index_mainloop] = '<div class="frame">'
            html.append('</div>')

        cmd, event = event.split('-', 1)

        # analyse commands 
        if cmd == 'mark':
            html.append('<div class="mark">{}: {}</div>'.format(
                event, escape(str(infos[2]))))
        elif cmd == 'start':
            index = len(html)
            html.append('')
            tags[event] = (time, index)
        elif cmd == 'end':
            start_time, index = tags[event]
            width = int((time - start_time) * WIDTH / (1 / 60.))
            offset = int((start_time - start_mainloop) * WIDTH / (1 / 60.))
            duration = (time - start_time)
            text = (
                '<div class="line line-{0}">'
                '<div class="line-header">{0}</div>'
                '<div class="line-time">{3:.2f}</div>'
                '<div class="line-content">'
                '<div class="block {0}" style="margin-left: {2}px; width: {1}px">'
                '<span>{0}</span></div>'
                '</div>'
                '</div>'
            ).format(event, width, offset, duration * 1000)

            if duration > 1. / 60.:
                text = '<div class="alert">' + text + '</div>'

            html[index] = text

    with open('output.html', 'w') as fd:
        fd.write(HTML_HEADER)
        fd.write(''.join(html))
        fd.write(HTML_FOOTER)


generate(argv[1])

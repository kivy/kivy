import sys
from glob import glob
from os.path import join, dirname
from kivy.uix.scatter import Scatter
from kivy.app import App
from kivy.graphics.svg import Svg
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.clock import mainthread

try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    watchdog = None

Builder.load_string("""
<SvgWidget>:
    do_rotation: False

<FloatLayout>:
    canvas.before:
        Color:
            rgb: (1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
""")


class SvgWidget(Scatter):

    def __init__(self, filename, **kwargs):
        super(SvgWidget, self).__init__(**kwargs)
        self.canvas.clear()
        with self.canvas:
            self.svg = svg = Svg(filename)
        self.size = svg.width, svg.height


class SvgApp(App):

    def build(self):
        self.root = FloatLayout()

        filenames = sys.argv[1:]
        if not filenames:
            filenames = glob(join(dirname(__file__), '*.svg'))

        watchers = {}
        for filename in filenames:
            svg = SvgWidget(filename, size_hint=(None, None))
            watchers[filename] = svg
            self.root.add_widget(svg)
            # svg.scale = 5.
            svg.center = Window.center

        if watchdog:
            observer = Observer()
            event_handler = SVGReloader(watchers=watchers)
            # XXX better to either watch the dirs of all the files, or
            # the last common directory of all the files
            observer.schedule(event_handler, path='.', recursive=True)
            observer.start()

    @mainthread
    def _reload(self, svg):
        svg.svg.filename = svg.svg.filename
        svg.canvas.ask_update()
        print("{} should be reloaded".format(svg))


    @mainthread
    def _reload_shader(self, svgs):
        print('shaders changed…')
        with open('./kivy/data/glsl/svg_fs.glsl') as f:
            fs = f.read()
        with open('./kivy/data/glsl/svg_vs.glsl') as f:
            vs = f.read()

        for svg in svgs:
            svg.svg.shader.fs = fs
            svg.svg.shader.vs = vs
            svg.canvas.ask_update()


if watchdog:
    class SVGReloader(FileSystemEventHandler):
        def __init__(self, *args, watchers=None, **kwargs):
            self.__watchers = watchers

        def __handle(self, event):
            print('{} created'.format(event.src_path))
            svg = self.__watchers.get(event.src_path)
            if svg:
                app._reload(svg)
            elif event.src_path in (
                './kivy/data/glsl/svg_fs.glsl',
                './kivy/data/glsl/svg_vs.glsl',
            ):
                app._reload_shader(self.__watchers.values())

        def on_modified(self, event):
            self.__handle(event)

        def on_created(self, event):
            self.__handle(event)


if __name__ == '__main__':
    app = SvgApp()
    app.run()

from kivy.app import App
from kivy.lang import Builder


kv = '''
BoxLayout:
    orientation: 'vertical'

    Camera:
        id: camera
        resolution: 399, 299

    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '48dp'
        Button:
            text: 'Start'
            on_release: camera.play = True

        Button:
            text: 'Stop'
            on_release: camera.play = False
'''


class CameraApp(App):
    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    CameraApp().run()

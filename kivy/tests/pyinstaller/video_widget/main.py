from project import VideoApp

if __name__ == '__main__':
    from kivy.core.video import Video
    assert Video is not None
    VideoApp().run()
